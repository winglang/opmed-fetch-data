from urllib.parse import parse_qs

from utils.jwt_utils import validate_jwt, generate_401_response


def validate_view_blocks_handler(event, context):
    request = event['Records'][0]['cf']['request']

    print(request)

    symmetric_key = request['headers'].pop('Symmetric-Key')[0]['value']

    query_params = {k: v[0] for k, v in parse_qs(request['querystring']).items()}
    jwt = query_params.get('token')

    jwt_payload = validate_jwt(jwt, symmetric_key)

    if not jwt_payload:
        return generate_401_response()

    if 'headers' not in request:
        request['headers'] = {}
    request['headers']['User-Id'] = [{'key': 'User-Id', 'value': jwt_payload['user_id']}]
    request['headers']['Tenant-Id'] = [{'key': 'Tenant-Id', 'value': jwt_payload['org_id']}]
    return request
