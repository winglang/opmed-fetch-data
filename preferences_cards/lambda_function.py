import datetime
import json
import os
from decimal import Decimal

from utils.dynamodb_accessor import DynamoDBAccessor
from utils.preferences_card_pkey import PreferencesCardsPKey
from utils.services_utils import (
    get_service,
    handle_error_response,
    lowercase_headers,
    get_username,
    create_error_response,
    valid_service,
)


def lambda_handler(event, context):
    print(event)

    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers'])

    print(f'username: {username}')

    for key in event:
        print(key)

    service = get_service(event)
    if not valid_service(service):
        return handle_error_response(service)

    # Extracting HTTP method and path from the event
    http_method = event['requestContext']['http']['method']
    path = event['requestContext']['http']['path']

    # Check if the method is GET and the path is /api/v1/preference-cards - list all objects.
    if http_method == 'GET' and path == '/api/v1/preference-cards':  # Note: without "/"
        parsed_data_ids = get_parsed_data_ids_for_tenant(service)
        print('Parsed Data IDs:', parsed_data_ids)
        return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(parsed_data_ids)}

    # For other cases, extracting procedure and surgeon from the path and perform "rest" operations.
    elif path.startswith('/api/v1/preference-cards/'):
        # Splitting the path to get the individual components
        _, _, _, _, procedure, surgeon = path.split('/')
        data_object = None
        if event is not None and 'body' in event and event['body'] is not None:
            data_object = json.loads(event['body'])
        try:
            result = handle_rest_request(http_method, service, procedure, surgeon, data_object)
            if result:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(result, default=dynamodb_decimal_default_encoder),
                }
            else:
                return create_error_response(500, 'Operation failed')
        except ValueError as e:
            print(f'Caught an error: {e}')
            return create_error_response(500, 'Invalid parameter')

    # Default response for other cases
    else:
        print(path)
        return create_error_response(400, 'Invalid request')


def get_parsed_data_ids_for_tenant(tenant_id):
    # Ensure that tenant_id is provided
    if not tenant_id:
        raise ValueError('Missing tenantId')

    # Initialize DynamoDB Accessor with your table name
    db_accessor = DynamoDBAccessor(os.environ['DYNAMODB_TABLE_NAME'])

    # Retrieve dataId values for the given tenant
    data_ids = db_accessor.list_data_ids_by_tenant(tenant_id)

    # Parse each data_id into procedure_id and surgeon_id
    parsed_ids = []
    for data_id in data_ids:
        if '$$' in data_id:
            procedure_id, surgeon_id = PreferencesCardsPKey.parse_key(data_id)
            parsed_ids.append({'procedure_id': procedure_id, 'surgeon_id': surgeon_id})
        else:
            print(f"Warning: data_id '{data_id}' does not contain expected separator '$$'")

    return parsed_ids


def handle_rest_request(http_method, tenant_id, procedure_id, surgeon_id, data):
    # Validate input
    if not tenant_id or not procedure_id or not surgeon_id:
        raise ValueError('Missing required parameters')

    # Combine procedure_id and surgeon_id into dataId
    data_id = PreferencesCardsPKey.generate_key(procedure_id, surgeon_id)

    # Initialize the DynamoDB accessor
    db_accessor = DynamoDBAccessor(os.environ['DYNAMODB_TABLE_NAME'])

    metadata = {}
    if data is not None:
        # Get current time as unix time in milliseconds
        now = datetime.datetime.now()
        timestamp = int(now.timestamp() * 1000)
        metadata['lastUpdated'] = timestamp

    # Handle different HTTP methods
    if http_method == 'GET':
        # Retrieve an item
        item = db_accessor.get_item(tenant_id, data_id)
        if item is not None:
            return item['data']
        else:
            return None

    elif http_method == 'POST':
        # Create a new item
        # check that object does not exist before adding.
        item = db_accessor.get_item(tenant_id, data_id)
        if item is not None:
            raise ValueError(f'Resource already exist: {data_id}')
        return db_accessor.put_item(tenant_id, data_id, data, metadata=metadata)

    elif http_method == 'PUT':
        # Update an existing item
        return db_accessor.put_item(tenant_id, data_id, data, metadata=metadata)

    elif http_method == 'DELETE':
        # Delete an item
        return db_accessor.delete_item(tenant_id, data_id)

    else:
        raise ValueError(f'Unsupported HTTP method: {http_method}')


# Custom encoder function - duplicate code
def dynamodb_decimal_default_encoder(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # or use str(obj) if you want to preserve exactness
    raise TypeError
