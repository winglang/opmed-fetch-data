import json
import os
from datetime import datetime

import boto3

from utils.data_utils import CustomJSONEncoder
from utils.services_utils import get_service, Service, get_username, handle_error_response, lowercase_headers


def lambda_handler(event, context):
    print(f"event: {event}")

    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    # Unit test only!
    service = get_service(event)

    save_to_blob = False

    if event is not None and "body" in event and event["body"] is not None and "save" in event["body"]:
        save_to_blob = True
    if event is not None and "save" in event:
        save_to_blob = True

    if "queryStringParameters" in event and event["queryStringParameters"] is not None:
        if "save" in event["queryStringParameters"]:
            save_to_blob = event["queryStringParameters"]['save']

    if service == Service.FHIR.value or service.startswith(Service.FHIR.value):
        from connectors.FHIR.api import get_url, get_headers, update_data

    else:
        return handle_error_response(service)

    url = get_url()
    headers = get_headers(event)

    data = json.loads(event['body'])
    records_array = update_data(url, data, headers)
    if records_array is None:
        return handle_error_response({"statusCode": 200, "error": "fail to update data"})

    response_update = json.dumps(json.loads(records_array.text), cls=CustomJSONEncoder)

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


if __name__ == '__main__':
    event = {
        "body": {
            "cases": [
                {
                    "id": "appointment-1531",
                    "new": {
                        "roomId": "OR-5",
                        "startTime": "2023-06-15T07:0:00",
                        "endTime": "2023-06-15T8:30:00"
                    },
                    "old": {
                        "roomId": "OR-1",
                        "startTime": "2023-06-15T007:00:00",
                        "endTime": "2023-06-15T08:30:00"
                    }
                },
                {
                    "id": "appointment-2323",
                    "new": {
                        "roomId": "OR-5",
                        "startTime": "2023-06-15T08:30:00",
                        "endTime": "2023-06-15T11:15:00"
                    },
                    "old": {
                        "roomId": "OR-1",
                        "startTime": "2023-06-15T08:30:00",
                        "endTime": "2023-06-15T11:15:00"
                    }
                }
            ],
            "blocks": [
                {
                    "id": "slot-151",
                    "new": {
                        "roomId": "OR-5",
                        "startTime": "2023-06-15T07:00:00",
                        "endTime": "2023-06-15T11:30:00"
                    },
                    "old": {
                        "roomId": "OR-1",
                        "startTime": "2023-06-15T07:00:00",
                        "endTime": "2023-06-15T11:30:00"
                    }
                }
            ]
        }
    }

    lambda_handler(event, None)
