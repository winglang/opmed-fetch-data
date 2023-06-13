from datetime import datetime

import requests
from fhirpy import SyncFHIRClient

from models import BlockModelFetched, OperationModelFetched, ProcedureModel, CurrentProcedureModel


def create_surgery(appointment, patients_dict, blocks):
    patients_birth_date = patients_dict[appointment['participant'][1].actor.id].birthDate
    if not appointment.slot[0].id in blocks:
        return
    room_id = blocks[appointment.slot[0].id].resourceId
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
        anesthesia=''
    )


def create_block(block, blocks_main_surgeon_dict):
    return BlockModelFetched(
        id=block.id,
        start=block.start,
        end=block.end,
        resourceId=block['extension'][0].valueReference.id,
        title=block.id,
        doctor_name=blocks_main_surgeon_dict[block.id]['name'],
        doctor_id=blocks_main_surgeon_dict[block.id]['id']
    )


def get_url():
    return 'http://ec2-23-22-99-103.compute-1.amazonaws.com:80/fhir/'


def get_headers():
    headers = {
        "source": 'mock',
        "Content-Type": "application/fhir+json;charset=utf-8"
    }
    return headers


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
        'name': appointment['participant'][2].actor.display
    } for appointment in appointments}

    blocks = {block.id: create_block(block, blocks_main_surgeon_dict) for block in slots}

    surgeries = [create_surgery(appointment, patients_dict, blocks) for appointment in appointments]
    surgeries = [surgery for surgery in surgeries if surgery]

    return [item.dict() for item in list(blocks.values()) + surgeries]


def update_data(url, data, headers):
    resources = [
        {
            "fullUrl": f"urn:uuid:{resource['id']}",
            "resource": resource,
            "request": {"method": "PUT", "url": f"{resource['resourceType']}/{resource['id']}"}
        }
        for resource in data
    ]

    request_data = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": resources
    }

    return requests.post(url=url, data=request_data, headers=headers)

