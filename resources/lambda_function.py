import json
from utils.services_utils import get_service, Service, handle_error_response, lowercase_headers, get_username


def lambda_handler(event, context):
    print(event)

    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    for key in event:
        print(key)

    service = get_service(event)
    if service not in [Service.HMC.value, Service.FHIR.value, Service.MOCK.value,
                       Service.DEMO.value] and not service.startswith(Service.FHIR.value):
        return handle_error_response(service)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "last_modified": "test"
        })
    }
