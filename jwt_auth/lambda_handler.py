from urllib.parse import parse_qs

from utils.jwt_utils import get_jwt_from_db, validate_jwt, generate_401_response, generate_403_response


def validate_view_blocks_handler(event, context):
    request = event['Records'][0]['cf']['request']

    query_params = {k: v[0] for k, v in parse_qs(request['querystring']).items()}
    jwt = query_params.get('token')
    jwt_item = get_jwt_from_db(jwt)

    if not jwt_item or not validate_jwt(jwt):
        return generate_401_response()

    requested_blocks = query_params['block_ids']

    if set(requested_blocks).issubset(jwt_item['blocks_id']):
        return request
    else:
        return generate_403_response()
