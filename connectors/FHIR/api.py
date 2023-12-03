import base64
import json
from datetime import datetime

import requests
from fhirpy import SyncFHIRClient

from utils.models.fetch_data import BlockModelFetched, OperationModelFetched, ProcedureModel, CurrentProcedureModel


def create_surgery(appointment, patients_dict, blocks):
    patients_birth_date = patients_dict[appointment['participant'][1].actor.id].birthDate
    if not appointment.slot[0].id in blocks:
        return
    parent_block = blocks[appointment.slot[0].id]
    room_id = parent_block.resourceId
    return OperationModelFetched(
        id=appointment.id,
        start=appointment.start,
        end=appointment.end,
        resourceId=room_id,
        parent_block_id=appointment.slot[0].id,
        surgery_id=appointment.id,
        doc_name=appointment['participant'][2].actor.display,
        sur_name=appointment['description'],
        type=appointment['serviceType'][0].text,
        patient_age=round((datetime.now() - datetime.strptime(patients_birth_date, '%Y-%m-%d')).days / 365),
        procedure=ProcedureModel(
            current=[
                CurrentProcedureModel(
                    surgery_category=appointment['description'],
                    surgery_name=appointment['description'],
                    procedure=appointment['description'],
                    surgery_duration=appointment['minutesDuration'],
                    procedure_code=12345,
                    procedure_name=appointment['description'],
                    procedure_icd=12345
                )
            ]
        ),
        anesthesia='y' if parent_block.anesthetist_name else 'n'
    )


def create_block(block, blocks_main_surgeon_dict):
    return BlockModelFetched(
        id=block.id,
        start=block.start,
        end=block.end,
        resourceId=block['extension'][0].valueReference.id,
        title=block.id,
        doctor_name=blocks_main_surgeon_dict.get(block.id, {}).get('surgeon', 'placeholder'),
        doctor_id=blocks_main_surgeon_dict.get(block.id, {}).get('id', '123456789'),
        nurse_name=blocks_main_surgeon_dict.get(block.id, {}).get('nurses', None),
        anesthetist_name=blocks_main_surgeon_dict.get(block.id, {}).get('anesthetist', None)
    )


def get_url():
    return 'http://ec2-23-22-99-103.compute-1.amazonaws.com:80/fhir/'


def get_headers():
    headers = {
        "source": 'mock',
        "Content-Type": "application/fhir+json;charset=utf-8"
    }
    return headers


def zip_names_and_ids(practitioners):
    return ','.join([f'{practitioner.actor.id} - {practitioner.actor.display}' for practitioner in practitioners])


def get_data(url, data, headers):
    client = SyncFHIRClient(
        url
    )

    appointments = client.resources("Appointment").search(date__ge=data['start'], date__lt=data['end'], status="booked",
                                                          _count=10 ** 5).fetch()

    slots = client.resources("Slot").search(start__ge=data['start'], start__lt=data['end'], _count=10 ** 5).fetch()

    patients_dict = {patient.id: patient for patient in client.resources("Patient").search(_count=10 ** 5).fetch()}

    blocks_main_surgeon_dict = {appointment.slot[0].id: {
        'id': appointment['participant'][2].actor.id,
        'surgeon': appointment['participant'][2].actor.display,
        'nurses': zip_names_and_ids(appointment['participant'][3:5]),
        'anesthetist': zip_names_and_ids([appointment['participant'][5]]) if len(
            appointment['participant']) > 5 else None
    } for appointment in appointments}

    blocks = {block.id: create_block(block, blocks_main_surgeon_dict) for block in slots}

    surgeries = [create_surgery(appointment, patients_dict, blocks) for appointment in appointments]
    surgeries = [surgery for surgery in surgeries if surgery]

    return [item.dict() for item in list(blocks.values()) + surgeries]


def update_data(url, data, headers):
    slots = [dict(item, resource_type='Slot') for item in data['blocks']]
    appointments = [dict(item, resource_type='Appointment') for item in data['cases']]
    resources = slots + appointments

    entries = [
        {
            "resource": {
                "resourceType": "Binary",
                "contentType": "application/json-patch+json",
                "data": base64.b64encode(json.dumps(create_patch(resource)).encode('ascii')).decode('ascii')
            },
            "request": {
                "method": "PATCH",
                "url": f"{resource['resource_type']}/{resource['id']}"
            },
            "fullUrl": resource['id']
        }
        for resource in resources
    ]

    request_data = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": entries
    }

    return requests.post(url=url, data=json.dumps(request_data), headers=headers)


def create_patch(resource):
    resource_type = resource['resource_type']

    if resource_type == 'Slot':
        return create_slot_patch(resource['new'])
    elif resource_type == 'Appointment':
        return create_appointment_patch(resource['new'])
    else:
        return []


def create_slot_patch(slot):
    return [
        {
            "op": "replace",
            "path": "/extension/0",
            "value": {
                "valueReference": {
                    "reference": f"Location/{slot['roomId']}",
                    "display": slot['roomId']
                },
                "url": "http://example.com/extensions#location"
            }
        },
        {
            "op": "replace",
            "path": "/start",
            "value": datetime.strptime(slot['startTime'], '%Y-%m-%dT%H:%M:%S').isoformat()
        },
        {
            "op": "replace",
            "path": "/end",
            "value": datetime.strptime(slot['endTime'], '%Y-%m-%dT%H:%M:%S').isoformat()
        }
    ]


def create_appointment_patch(appointment):
    return [
        {
            "op": "replace",
            "path": "/participant/0/actor",
            "value": {
                "reference": f"Location/{appointment['roomId']}",
                "display": appointment['roomId']
            }

        },
        {
            "op": "replace",
            "path": "/start",
            "value": datetime.strptime(appointment['startTime'], '%Y-%m-%dT%H:%M:%S').isoformat()
        },
        {
            "op": "replace",
            "path": "/end",
            "value": datetime.strptime(appointment['endTime'], '%Y-%m-%dT%H:%M:%S').isoformat()
        }
        ,
        {
            "op": "replace",
            "path": "/minutesDuration",
            "value": (datetime.strptime(appointment['endTime'], '%Y-%m-%dT%H:%M:%S') - datetime.strptime(
                appointment['startTime'], '%Y-%m-%dT%H:%M:%S')).total_seconds() // 60
        }
    ]
