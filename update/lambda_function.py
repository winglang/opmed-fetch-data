import json
import os
from datetime import datetime

import boto3

from services import get_service, Service
from utils import CustomJSONEncoder


def lambda_handler(event, context):
    # Unit test only!
    service = get_service(event, None)

    save_to_blob = False

    if event is not None and "body" in event and event["body"] is not None and "save" in event["body"]:
        save_to_blob = True
    if event is not None and "save" in event:
        save_to_blob = True

    if "queryStringParameters" in event and event["queryStringParameters"] is not None:
        if "service" in event["queryStringParameters"]:
            service = event["queryStringParameters"]['service']
        if "save" in event["queryStringParameters"]:
            save_to_blob = event["queryStringParameters"]['save']

    if service == Service.FHIR.value:
        from FHIR.api import get_url, get_headers, update_data

    else:
        return {
            "statusCode": 401,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {"error": "invalid group"}
        }

    url = get_url()
    headers = get_headers()

    data = event['body']
    records_array = update_data(url, data, headers)
    if records_array is None:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {"error": "fail to fetch data"}
        }

    response_update = json.dumps(records_array, cls=CustomJSONEncoder)

    if save_to_blob:
        try:
            s3 = boto3.resource('s3')
            s3object = s3.Object(os.environ['BUCKET_NAME'],
                                 'update.{}.json'.format(datetime.now().strftime("%Y%m%d%H%M%S")))
            s3object.put(
                Body={
                    "request data": data,
                    "response": response_update
                }
            )
            print("Success: Saved to S3")
        except Exception as e:
            print("Error: {}".format(e))

    # Print response
    print(response_update)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": response_update

    }
