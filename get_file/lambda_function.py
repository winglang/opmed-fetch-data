import json
import logging
import os

import boto3

from utils.services_utils import get_service, Service, handle_error_response, lowercase_headers, get_username


def create_presigned_url(bucket_name, object_name, expiration=600):
    s3_client = boto3.client('s3', region_name=os.environ['REGION'],
                             config=boto3.session.Config(signature_version='s3v4', ))
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        logging.error(e)
        return "Error"

    return response


def get_last_modified(bucket_name, object_name):
    s3_client = boto3.client('s3', region_name=os.environ['REGION'],
                             config=boto3.session.Config(signature_version='s3v4', ))
    try:
        return s3_client.head_object(Bucket=bucket_name, Key=object_name)['LastModified'].timestamp() * 1e3
    except Exception as e:
        print(e)
        logging.error(e)
        return "Error"


def lambda_handler(event, context):
    print(event)

    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    for key in event: print(key)
    if 'queryStringParameters' not in event: return
    if 'file' not in event['queryStringParameters']: return

    service = get_service(event)
    if service not in [Service.HMC.value, Service.FHIR.value, Service.MOCK.value, Service.DEMO.value]:
        return handle_error_response(service)

    s3_path = os.getenv('prefix', '') + service + "/" + event['queryStringParameters']['file']
    url = create_presigned_url(os.environ['BUCKET'], s3_path, os.environ['EXPIRATION'])
    last_modified = get_last_modified(os.environ['BUCKET'], s3_path)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "url": url,
            "last_modified": last_modified
        })
    }
