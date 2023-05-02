from enum import Enum


class Service(Enum):
    HMC = "hmc-users"
    FHIR = "fhir-users"
    MOCK = "mock-users"


def get_user_groups(event):
    try:
        # Access the 'cognito:groups' claim from the authorizer context
        groups = event['requestContext']['authorizer']['claims']['cognito:groups']

        # Return the groups as a list
        return groups

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

