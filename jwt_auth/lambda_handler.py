from urllib.parse import parse_qs

from utils.jwt_utils import get_jwt_from_db, validate_jwt, generate_401_response, generate_403_response


def validate_view_blocks_handler(event, context):
    request = event['Records'][0]['cf']['request']

    symmetric_key = request['headers'].pop('Symmetric-Key')[0]['value']
    jwt_table_name = request['headers'].pop('Jwt-Table-Name')[0]['value']

    query_params = parse_qs(request['querystring'])
    jwt = query_params.get('token')[0]
    jwt_item = get_jwt_from_db(jwt, jwt_table_name)

    jwt_payload = validate_jwt(jwt, symmetric_key)

    if not jwt_item or not jwt_payload:
        return generate_401_response()

    requested_blocks = query_params['ids']

    if set(requested_blocks).issubset(jwt_item['blocks_id']):
        if 'headers' not in request:
            request['headers'] = {}
        request['headers']['User-Id'] = [{'key': 'User-Id', 'value': jwt_payload['user_id']}]
        request['headers']['Tenant-Id'] = [{'key': 'Tenant-Id', 'value': jwt_payload['org_id']}]
        return request
    else:
        return generate_403_response()
