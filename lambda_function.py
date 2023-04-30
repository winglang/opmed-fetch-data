import json
import os
import datetime
import boto3

from models.block_model_fetched import BlockModelFetched
from models.operation_model_fetched import OperationModelFetched
from services import get_service, Service

MAX_DELTA_DAYS = 370


def filter_data(item, whitelist):
    return {key: item[key] for key in whitelist if key in item}


def lambda_handler(event, context):
    service = get_service(event, None)

    if service == Service.HMC.value:
        from HMC.fetch import get_url, get_headers, get_data
    elif service == Service.FHIR.value:
        from FHIR.fetch import get_url, get_headers, get_data
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

    today = datetime.date.today()
    from_date = default_from_date = today - datetime.timedelta(days=3)
    to_date = default_to_date = today + datetime.timedelta(days=21)
    save_to_blob = False

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
            save_to_blob = True

    delta_days = to_date - from_date
    if delta_days.days > MAX_DELTA_DAYS:
        from_date = default_from_date
        to_date = default_to_date

    data = {
        "event_type": "surgery",
        "start": from_date.strftime("%Y-%m-%d"),
        "end": to_date.strftime("%Y-%m-%d")
    }

    recordsArray = get_data(url, data, headers)
    if recordsArray is None:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {"error": "fail to fetch data"}
        }

    response_objects = []
    for item in recordsArray:
        if 'allDay' in item:
            filtered_data = filter_data(item, BlockModelFetched.swagger_types.keys())
            # response_objects.append(filtered_data)
            response_objects.append(BlockModelFetched(**filtered_data).to_dict())
        else:
            filtered_data = filter_data(item, OperationModelFetched.swagger_types.keys())
            # response_objects.append(filtered_data)
            response_objects.append(OperationModelFetched(**filtered_data).to_dict())

    response_fetch = json.dumps(response_objects)

    # Print response
    print(response_fetch)

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
