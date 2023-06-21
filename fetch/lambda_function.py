import json
import os
import datetime
import boto3

from utils.services_utils import get_service, Service
from utils.data_utils import CustomJSONEncoder

MAX_DELTA_DAYS = 370


def lambda_handler(event, context):
    today = datetime.date.today()
    from_date = default_from_date = today - datetime.timedelta(days=3)
    to_date = default_to_date = today + datetime.timedelta(days=21)
    save_to_blob = False

    # Unit test only!
    service = get_service(event, None)

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
    elif service == Service.FHIR.value:
        from connectors.FHIR.api import get_url, get_headers, get_data
    elif service == Service.MOCK.value:
        from connectors.MOCK.fetch import get_url, get_headers, get_data
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

    records_array = get_data(url, data, headers)
    if records_array is None:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {"error": "fail to fetch data"}
        }

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
