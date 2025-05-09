import json
import os
from datetime import datetime

import boto3

from utils.services_utils import get_service, handle_error_response, lowercase_headers, valid_service


def get_list_by_service(prefix):
    if os.getenv('env', None) == 'local':
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            config=boto3.session.Config(signature_version='s3v4'),
        )
    else:
        s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))

    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=os.getenv('BUCKET'), Prefix=prefix)

    object_list = [object_file for page in page_iterator for object_file in page['Contents']]
    for object_file in object_list:
        object_file['Key'] = object_file['Key'].replace(prefix, '')
    return object_list


def lambda_handler(event, context):
    print({'event': event})

    if lowercase_headers(event):
        return lowercase_headers(event)

    service = get_service(event)
    if not valid_service(service):
        return handle_error_response(service)

    if 'rawPath' in event:
        path = event['rawPath']
    elif 'path' in event:
        path = event['path']
    method = path.rsplit('/', 1)[-1]
    if method == 'get-list-cache':
        method = 'alternative-plans'

    if event.get('queryStringParameters', {}) and event.get('queryStringParameters', {}).get('allocations', False):
        method = 'block-allocation'

    objects_list = get_list_by_service(f'lambda/{service}/{method}/')

    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return json.JSONEncoder.default(self, obj)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'list': objects_list}, cls=DateEncoder),
    }
