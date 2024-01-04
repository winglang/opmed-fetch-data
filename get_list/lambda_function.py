import json
import os
from datetime import datetime

import boto3

from utils.services_utils import get_service, Service, handle_error_response, lowercase_headers, get_username


def get_list_by_service(prefix):
    if os.getenv('env', None) == 'local':
        s3_client = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                 config=boto3.session.Config(signature_version='s3v4'))
    else:
        s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))

    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=os.getenv('BUCKET'), Prefix=prefix)

    object_list = [object_file for page in page_iterator for object_file in page['Contents']]
    for object_file in object_list:
        object_file['Key'] = object_file['Key'].replace(prefix, '')
    return object_list


def lambda_handler(event, context):
    print(event)

    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    service = get_service(event)
    if service not in [Service.HMC.value, Service.FHIR.value, Service.MOCK.value,
                       Service.DEMO.value] and not service.startswith(Service.FHIR.value):
        return handle_error_response(service)

    method = event['path'].rsplit('/', 1)[-1]
    if method == 'get-list-cache':
        method = 'alternative_plans'

    objects_list = get_list_by_service(f'lambda/{service}/{method}/')

    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return json.JSONEncoder.default(self, obj)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "list": objects_list
        }, cls=DateEncoder)
    }
