import os
import json
import logging
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


def lambda_handler(event, context):
    print(event)

    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    for key in event: print(key)
    if 'queryStringParameters' not in event: return
    if 'file' not in event['queryStringParameters']: return

    # Unit test only!
    service = get_service(event)
    if service == Service.HMC.value:
        prefix = "HMC"
    elif service == Service.FHIR.value:
        prefix = "FHIR"
    elif service == Service.MOCK.value:
        prefix = "MOCK"
    elif service == Service.DEMO.value:
        prefix = "DEMO"
    else:
        return handle_error_response(service)

    s3_path = prefix + "/" + event['queryStringParameters']['file']
    url = create_presigned_url(os.environ['BUCKET'], s3_path, os.environ['EXPIRATION'])

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "url": url
        })
    }
