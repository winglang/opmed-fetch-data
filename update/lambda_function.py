import json

from services import get_service, Service
from utils import CustomJSONEncoder

MAX_DELTA_DAYS = 370


def lambda_handler(event, context):
    # Unit test only!
    service = get_service(event, None)

    if "queryStringParameters" in event and event["queryStringParameters"] is not None:
        if "service" in event["queryStringParameters"]:
            service = event["queryStringParameters"]['service']

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

    records_array = update_data(url, event['body'], headers)
    if records_array is None:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {"error": "fail to fetch data"}
        }

    response_update = json.dumps(records_array, cls=CustomJSONEncoder)

    # Print response
    print(response_update)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": response_update

    }
