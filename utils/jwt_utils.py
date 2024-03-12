import os
from datetime import timezone, datetime, timedelta
from urllib.parse import parse_qs

import boto3
import jwt

symmetric_key = os.getenv('SYMMETRIC_KEY')
jwt_table_name = os.getenv('JWT_TABLE_NAME')

algorithm = 'HS512'


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


def generate_401_response():
    return {
        'status': '401',
        'statusDescription': 'Unauthorized',
        'headers': {'content-type': [{'key': 'Content-Type', 'value': 'text/plain'}]},
        'body': 'Unauthorized: Access is denied due to invalid credentials.'
    }


def generate_403_response():
    return {
        'status': '403',
        'statusDescription': 'Forbidden',
        'headers': {'content-type': [{'key': 'Content-Type', 'value': 'text/plain'}]},
        'body': 'Forbidden: Access is denied due to lack of permission'
    }


def generate_jwt(tenant_id, user_id):
    payload = {
        "user_id": user_id,
        "org_id": tenant_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=2),  # Setting expiration to one day
        "iat": datetime.now(timezone.utc)
    }

    encoded_jwt = jwt.encode(payload, symmetric_key, algorithm=algorithm)

    return encoded_jwt


def store_jwt(jwt, blocks_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(jwt_table_name)

    item = {
        'id': jwt,
        'blocks_id': blocks_id,
        'expired_at': int((datetime.now() + timedelta(days=2)).timestamp())
    }

    return table.put_item(Item=item)


def get_jwt_from_db(jwt):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(jwt_table_name)

    try:
        response = table.get_item(Key={'id': jwt})
        return response.get('Item')
    except Exception as e:
        print(f"Error reading from DynamoDB: {e}")


def validate_jwt(token):
    try:
        decoded = jwt.decode(token, symmetric_key, algorithms=[algorithm])
    except Exception as e:
        print(e)
        return False
    return decoded
