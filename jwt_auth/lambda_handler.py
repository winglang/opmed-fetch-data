from urllib.parse import parse_qs

from utils.jwt_utils import get_jwt_from_db, validate_jwt, generate_401_response, generate_403_response


def validate_view_blocks_handler(event, context):
    request = event['Records'][0]['cf']['request']

    query_params = {k: v[0] for k, v in parse_qs(request['querystring']).items()}
    jwt = query_params.get('token')
    jwt_item = get_jwt_from_db(jwt)

    jwt_payload = validate_jwt(jwt)

    if not jwt_item or not jwt_payload:
        return generate_401_response()

    requested_blocks = query_params['block_ids']

    if set(requested_blocks).issubset(jwt_item['blocks_id']):
        if 'headers' not in request:
            request['headers'] = {}
        request['headers']['doctor-id'] = [{'key': 'Doctor-Id', 'value': jwt_item['user_id']}]
        request['headers']['tenant-id'] = [{'key': 'Tenant-Id', 'value': jwt_item['org_id']}]
        return request
    else:
        return generate_403_response()
