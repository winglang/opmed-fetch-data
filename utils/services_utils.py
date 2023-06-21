import base64
import json
from enum import Enum


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
        cookies = event['headers']['Cookie']
        return get_service_id_from_cognito_cookies(cookies)

    except KeyError as e:
        # If the 'cognito:groups' claim is not present in the authorizer context, return an empty list
        print("Error: ", e)
        return []

    except Exception as e:
        # Handle any other exceptions that might occur
        print("Error: ", e)
        return []


def get_service(event, requested_service=None):
    try:
        # Get the list of user groups from the authorizer context
        groups = get_user_groups(event)

        # If the groups list is empty or has no items, return None
        if not groups or len(groups) == 0:
            return None

        # If the requested service is not provided, return the first group in the list
        if requested_service is None:
            return groups[0]

        # If the requested service is found in the list of groups, return it
        if requested_service in groups:
            return requested_service

        # If the requested service is not found in the list of groups, return None
        return None

    except Exception as e:
        # Handle any errors that may occur and return None
        print("Error: ", e)
        return None
