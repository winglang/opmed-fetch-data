import base64
import json
from enum import Enum
from urllib.parse import urlparse

DOMAIN_TO_USER_GROUPS = {
    'plannerd.greatmix.ai': {"hmc-users", "fhir-users", "umh-users"},
    'planners.greatmix.ai': {"hmc-users", "fhir-users", "umh-users"},
    'planner.greatmix.ai': {"hmc-users"},
    'demo.greatmix.ai': {"demo-users"},
    'fhir.greatmix.ai': {"fhir-users"},
    'umh-dev.greatmix.ai': {"umh-users"},
    'umh.greatmix.ai': {"umh-users"}
}


class Service(Enum):
    HMC = "hmc-users"
    FHIR = "fhir-users"
    MOCK = "mock-users"
    DEMO = "demo-users"


def get_service_ids_from_cognito_jwt(jwt: dict) -> [str]:
    return jwt.get("cognito:groups", [""])


def get_service_id_from_cognito_cookies(cookies: str) -> str:
    try:
        cookies_array = [c for c in cookies.split("; ") if "CognitoIdentityServiceProvider" in c and "accessToken" in c]
        if len(cookies_array) != 1:
            raise Exception("Invalid number of cookies")
        JWT = cookies_array[0].split("=")[1]
        jwt_payload = json.loads(base64.urlsafe_b64decode(JWT.split(".")[1] + "==="))
        x = get_service_ids_from_cognito_jwt(jwt_payload)
        return x
    except Exception as e:
        print(e, "cookies error")
        return ""


def get_username(cookies: str) -> str:
    try:
        cookies_array = [c for c in cookies.split("; ") if "CognitoIdentityServiceProvider" in c and "accessToken" in c]
        if len(cookies_array) != 1:
            raise Exception("Invalid number of cookies")
        JWT = cookies_array[0].split("=")[1]
        jwt_payload = json.loads(base64.urlsafe_b64decode(JWT.split(".")[1] + "==="))
        return jwt_payload['username']
    except Exception as e:
        print(e, "cookies error")
        return ""


def get_user_groups(event):
    try:
        # Read JWT from cookie (user is authenticated in CF using that cookie)
        cookies = event['headers']['cookie']
        return get_service_id_from_cognito_cookies(cookies)

    except KeyError as e:
        # If the 'cognito:groups' claim is not present in the authorizer context, return an empty list
        print("Error: ", e)
        return []

    except Exception as e:
        # Handle any other exceptions that might occur
        print("Error: ", e)
        return []


def handle_error_response(error_response):
    return {
        "statusCode": error_response['statusCode'],
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({"error": error_response['error']})
    }


def get_service(event):
    try:
        headers = {"gmix_serviceid", "referer", "cookie"}
        event['headers'] = {k.lower(): v for k, v in event['headers'].items()}

        # check if all headers are received
        if headers.difference(event['headers']):
            return {"statusCode": 400, "error": f'missing headers: {headers.difference(event["headers"])}'}

        # Get the list of user groups from the authorizer context
        groups = get_user_groups(event)

        username = get_username(event['headers']['cookie'])

        domain = urlparse(event['headers']['referer']).hostname

        # If requested domain is unrecognized, return 404
        if domain not in DOMAIN_TO_USER_GROUPS:
            return {"statusCode": 404, "error": f'invalid domain: {domain}'}

        requested_service = event['headers']['gmix_serviceid']

        if requested_service not in groups:
            return {"statusCode": 401, "error": f'{username} is not a member of {requested_service}'}

        allowed_groups = DOMAIN_TO_USER_GROUPS[domain].intersection(set(groups))

        # If user is not allowed to domain, return 401
        if not allowed_groups:
            return {"statusCode": 401, "error": f'{username} unauthorized to access {domain}'}

        # If the requested service is found in the list of groups, return it
        if requested_service in allowed_groups:
            return requested_service

        # If the requested service is not found in the list of groups, return 401
        return {"statusCode": 401, "error": f'{username} unauthorized to access {requested_service} in domain {domain}'}

    except Exception as e:
        # Handle any errors that may occur and return None
        print("Error: ", e)
        return {"statusCode": 500, "error": e}
