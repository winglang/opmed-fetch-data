import base64
import json
from enum import Enum
from urllib.parse import urlparse

DOMAIN_TO_USER_GROUPS = {
    'plannerd.greatmix.ai': {
        'hmc-users',
        'fhir-users',
        'umh-users',
        'opmed-sandbox-5-ORs',
        'opmed-sandbox-10-ORs',
        'opmed-sandbox-20-ORs',
        'opmed-sandbox-30-ORs',
        'opmed-sandbox-40-ORs',
        'mayo-users',
        'nbi-users',
    },
    'planners.greatmix.ai': {'hmc-users', 'fhir-users', 'umh-users'},
    'planner.greatmix.ai': {'hmc-users'},
    'demo.greatmix.ai': {'demo-users'},
    'fhir.greatmix.ai': {'fhir-users'},
    'mayo.opmed.ai': {'mayo-users'},
    'nbi.opmed.ai': {'nbi-users'},
    'umh-dev.greatmix.ai': {'umh-users'},
    'umh.greatmix.ai': {'umh-users'},
    'plan.opmed.ai': {'hmc-users', 'mayo-users'},
    'mayo-hrs.opmed.ai': {'mayo-users'},
}

AUTH_HEADERS = {'gmix_serviceid', 'referer', 'cookie'}
JWT_HEADERS = {'tenant-id', 'user-id'}


class Service(Enum):
    HMC = 'hmc-users'
    FHIR = 'fhir-users'
    MAYO = 'mayo-users'
    NBI = 'nbi-users'
    MOCK = 'mock-users'
    DEMO = 'demo-users'
    SANDBOX = 'opmed-sandbox'


def valid_service(service):
    if type(service) is not str:
        return False
    return service in [x.value for x in Service] or service.startswith(Service.SANDBOX.value)


def get_service_ids_from_cognito_jwt(jwt: dict) -> [str]:
    return jwt.get('cognito:groups', [''])


def get_service_id_from_cognito_cookies(cookies: str) -> str:
    try:
        cookies_array = [c for c in cookies.split('; ') if 'CognitoIdentityServiceProvider' in c and 'accessToken' in c]
        if len(cookies_array) != 1:
            raise Exception('Invalid number of cookies')
        JWT = cookies_array[0].split('=')[1]
        jwt_payload = json.loads(base64.urlsafe_b64decode(JWT.split('.')[1] + '==='))
        x = get_service_ids_from_cognito_jwt(jwt_payload)
        return x
    except Exception as e:
        print(e, 'cookies error')
        return ''


def get_username(headers: dict) -> str:
    if username := headers.get('user-id', None):
        return username
    cookies = headers.get('cookie')
    try:
        cookies_array = [c for c in cookies.split('; ') if 'CognitoIdentityServiceProvider' in c and 'accessToken' in c]
        if len(cookies_array) != 1:
            raise Exception('Invalid number of cookies')
        JWT = cookies_array[0].split('=')[1]
        jwt_payload = json.loads(base64.urlsafe_b64decode(JWT.split('.')[1] + '==='))
        return jwt_payload['username']
    except Exception as e:
        print(e, 'cookies error')
        return ''


def get_cookie_exp(cookies: str) -> str:
    try:
        cookies_array = [c for c in cookies.split('; ') if 'CognitoIdentityServiceProvider' in c and 'accessToken' in c]
        if len(cookies_array) != 1:
            raise Exception('Invalid number of cookies')
        JWT = cookies_array[0].split('=')[1]
        jwt_payload = json.loads(base64.urlsafe_b64decode(JWT.split('.')[1] + '==='))
        return jwt_payload['exp']
    except Exception as e:
        print(e, 'cookies error')
        return ''


def get_user_groups(event):
    try:
        # Read JWT from cookie (user is authenticated in CF using that cookie)
        cookies = event['headers']['cookie']
        return get_service_id_from_cognito_cookies(cookies)

    except KeyError as e:
        # If the 'cognito:groups' claim is not present in the authorizer context, return an empty list
        print('Error: ', e)
        return []

    except Exception as e:
        # Handle any other exceptions that might occur
        print('Error: ', e)
        return []


def handle_error_response(error_response):
    return create_error_response(error_response['statusCode'], error_response['error'])


def create_error_response(status_code, error_msg):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': error_msg}),
    }


def get_service(event):
    if tenant_id := event.get('headers', {}).get('tenant-id', None):
        return tenant_id
    try:
        if lowercase_headers(event):
            return lowercase_headers(event)

        # Get the list of user groups from the authorizer context
        groups = get_user_groups(event)

        username = get_username(event['headers'])

        domain = urlparse(event['headers']['referer']).hostname

        # If requested domain is unrecognized, return 404
        if domain not in DOMAIN_TO_USER_GROUPS:
            return {'statusCode': 404, 'error': f'invalid domain: {domain}'}

        allowed_groups = DOMAIN_TO_USER_GROUPS[domain].intersection(set(groups))

        # If user is not allowed to domain, return 401
        if not allowed_groups:
            return {'statusCode': 401, 'error': f'{username} unauthorized to access {domain}'}

        # return data if domain is single tenant
        if len(DOMAIN_TO_USER_GROUPS[domain]) == 1:
            return next(iter(DOMAIN_TO_USER_GROUPS[domain]))

        requested_service = event['headers']['gmix_serviceid']

        if requested_service not in groups:
            return {'statusCode': 401, 'error': f'{username} is not a member of {requested_service}'}

        # If the requested service is found in the list of groups, return it
        if requested_service in allowed_groups:
            return requested_service

        # If the requested service is not found in the list of groups, return 401
        return {'statusCode': 401, 'error': f'{username} unauthorized to access {requested_service} in domain {domain}'}

    except Exception as e:
        # Handle any errors that may occur and return None
        print('Error: ', e)
        return {'statusCode': 500, 'error': e}


def get_auth_cookie_data(event):
    try:
        if lowercase_headers(event):
            return lowercase_headers(event)

        # Get the list of user groups from the authorizer context
        groups = get_user_groups(event)
        username = get_username(event['headers'])
        exp = get_cookie_exp(event['headers']['cookie'])
        domain = urlparse(event['headers']['referer']).hostname

        # If the requested service is not found in the list of groups, return 401
        return {
            'username': username,
            'domain': domain,
            'groups': groups,
            'exp': exp,
        }

    except Exception as e:
        # Handle any errors that may occur and return None
        print('Error: ', e)
        return {'statusCode': 500, 'error': e}


def lowercase_headers(event):
    event['headers'] = {k.lower(): v for k, v in event['headers'].items()}

    # check if all headers are received
    if AUTH_HEADERS.difference(event['headers']) and JWT_HEADERS.difference(event['headers']):
        return {
            'statusCode': 400,
            'error': f'missing headers: {AUTH_HEADERS.difference(event["headers"])} or {JWT_HEADERS.difference(event["headers"])}',
        }
