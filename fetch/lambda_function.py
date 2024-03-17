import datetime
import json
import os

import boto3

from utils.data_utils import CustomJSONEncoder
from utils.hash_utils import generate_sha256_hash
from utils.services_utils import get_service, Service, handle_error_response, lowercase_headers, get_username

MAX_DELTA_DAYS = 370

SALT = os.getenv('HASH_ID_SALT')


def is_block(record):
    return not is_task(record)


def is_task(task):
    return 'parent_block_id' in task


def convert_block_algo_model(block):
    block = {k: v or '' for k, v in block.items()}
    algo_model_block = {
        'start': block['start'],
        'end': block['end'],
        'hash_nurse_name': [nurse.split(' - ')[0] for nurse in
                            block['nurse_name'].split(',') if
                            nurse],
        'hash_sanitaire_name': [sanitaire.split(' - ')[0] for sanitaire in
                                block['sanitaire_name'].split(',') if sanitaire],
        'hash_assistant_name': [assistant.split(' - ')[0] for assistant in
                                block['assistant_name'].split(',') if assistant],
        'hash_anesthetist_name': [anesthetist.split(' - ')[0] for anesthetist in
                                  block['anesthetist_name'].split(',') if anesthetist],
        'hash_title': generate_sha256_hash(block['title'], SALT),
        # Patch: Some tenants send doctors names in the title which we want to hide.
        'resourceId': block['resourceId'],
        'id': block['id'],
        'doctor_id': block['doctor_id'],
        'doctors_license': generate_sha256_hash(block['doctors_license'], SALT),

    }

    return algo_model_block


def convert_task_algo_model(task, i, parent_block):
    task = {k: v or '' for k, v in task.items()}
    algo_model_task = {
        'start': task['start'],
        'end': task['end'],
        'hash_doc_name': generate_sha256_hash(task['doc_name'], SALT),
        'incrementalNumber': i,
        'resourceId': task['resourceId'],
        'id': task['id'],
        'surgery_id': task['surgery_id'],
        'parent_block_id': task['parent_block_id'],
        'procedure': task['procedure'],
        'procedure_icd': task['procedure']['current'][0]['procedure_icd'],
        'procedure_name': task['procedure']['current'][0]['procedure_name'],
        'surgery_name': task['procedure']['current'][0]['surgery_name'],
        'type': task['procedure']['current'][0]['surgery_name'].split(' > ')[-1],
        'patient_age': task['patient_age'],
        'anesthesia': task['anesthesia'],
        'resources_ids': {
            resource: parent_block.get(f'hash_{resource}_name') for resource in
            ['nurse', 'sanitaire', 'assistant', 'anesthetist'] if parent_block.get(f'hash_{resource}_name')
        },
        'xray_type': task.get('xray_type'),
        'xray_type_value': task.get('xray_type_value'),
        'tee_request': task.get('tee_request'),
        'heart_lung_machine_request': task.get('heart_lung_machine_request'),
        'additionalEquipment': task.get('additionalEquipment'),
        'sur_name': task.get('sur_name'),
        'doc_name': task.get('doc_name')
    }

    return algo_model_task


def convert_to_algo_model(fetch_data: list):
    blocks = {block['id']: convert_block_algo_model(block) for block in fetch_data if is_block(block)}
    tasks = [convert_task_algo_model(task, i, blocks[task['parent_block_id']]) for i, task in enumerate(fetch_data) if
             is_task(task)]

    fetch_data = {
        'blocks': list(blocks.values()),
        'tasks': tasks
    }
    return fetch_data


def lambda_handler(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers'])

    print(f'username: {username}')

    today = datetime.date.today()
    from_date = default_from_date = today - datetime.timedelta(days=3)
    to_date = default_to_date = today + datetime.timedelta(days=21)
    save_to_blob = False

    # Unit test only!
    service = get_service(event)

    print("event: {}".format(event))
    if event is not None and "body" in event and event["body"] is not None and "save" in event["body"]:
        save_to_blob = True
    if event is not None and "save" in event:
        save_to_blob = True

    if "queryStringParameters" in event and event["queryStringParameters"] is not None:
        if "from" in event["queryStringParameters"]:
            from_date = datetime.datetime.strptime(event["queryStringParameters"]["from"], "%Y-%m-%d")
        if "to" in event["queryStringParameters"]:
            to_date = datetime.datetime.strptime(event["queryStringParameters"]["to"], "%Y-%m-%d")
        if "save" in event["queryStringParameters"]:
            save_to_blob = event["queryStringParameters"]['save']

    delta_days = to_date - from_date
    if delta_days.days > MAX_DELTA_DAYS:
        from_date = default_from_date
        to_date = default_to_date

    data = {
        "event_type": "surgery",
        "start": from_date.strftime("%Y-%m-%d"),
        "end": to_date.strftime("%Y-%m-%d")
    }

    if service == Service.HMC.value:
        from connectors.HMC.fetch import get_url, get_headers, get_data
    elif service == Service.FHIR.value or service.startswith(Service.SANDBOX.value):
        from connectors.FHIR.api import get_url, get_headers, get_data
    elif service == Service.MOCK.value:
        from connectors.MOCK.fetch import get_url, get_headers, get_data
    else:
        return handle_error_response(service)

    url = get_url()
    headers = get_headers(event)

    records_array = get_data(url, data, headers)
    if records_array is None:
        return handle_error_response({"statusCode": 200, "error": "fail to fetch data"})

    method = event['path'].rsplit('/', 1)[-1]
    if method == 'v2':
        records_array = convert_to_algo_model(fetch_data=records_array)

    response_fetch = json.dumps(records_array, cls=CustomJSONEncoder)

    # Print response
    # print(response_fetch)

    if save_to_blob:
        try:
            s3 = boto3.resource('s3')
            s3object = s3.Object(os.environ['BUCKET_NAME'],
                                 'fetch.{}.json'.format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
            s3object.put(
                Body=response_fetch
            )
            print("Success: Saved to S3")
        except Exception as e:
            print("Error: {}".format(e))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": response_fetch

    }
