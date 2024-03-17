import datetime
import json
import os
from decimal import Decimal

from utils.dynamodb_accessor import DynamoDBAccessor
from utils.services_utils import get_service, handle_error_response, lowercase_headers, get_username, \
    create_error_response, valid_service, get_auth_cookie_data


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

    if not path.startswith('/api/v1/tenants-params'):
        print("Invalid path.")
        return create_error_response(400, 'Invalid request')

    # get the resource category.
    path_splits = path.split('/')
    if len(path_splits) not in [4, 5]:
        print("Invalid URL path length.")
        return create_error_response(400, 'Invalid request')

    # Check if the method is GET and the path is /api/v1/tenants-params - merge all objects to single json.
    if http_method == 'GET' and len(path_splits) == 4:
        all_data = get_all_data_for_tenant(service)
        print("Read all data. data:", all_data)
        auth = get_auth_cookie_data(event)
        return {
            'statusCode': 200,
            "headers": {
                "Content-Type": "application/json",
                "auth-data": json.dumps(auth)
            },
            'body': json.dumps(all_data, default=dynamodb_decimal_default_encoder)
        }

    else:  # For other cases, perform "rest" operations with the section id.
        # We handle only specific sections.
        valid_sections = ["equipments"]
        section_id = path_splits[5]
        if section_id not in valid_sections:
            return create_error_response(400, 'Invalid request')
        data_object = None
        if event is not None and "body" in event and event["body"] is not None:
            data_object = json.loads(event['body'])
        try:
            result = handle_rest_request(http_method, service, section_id, data_object)
            if result:
                return {
                    'statusCode': 200,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    'body': json.dumps(result, default=dynamodb_decimal_default_encoder)
                }
            else:
                return create_error_response(500, 'Operation failed')
        except ValueError as e:
            print(f"Caught an error: {e}")
            return create_error_response(500, 'Invalid parameter')


def get_table_name():
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    if table_name is None or table_name == "":
        raise ValueError("Missing env")
    return table_name


def get_all_data_for_tenant(tenant_id):
    # Ensure that tenant_id is provided
    if not tenant_id:
        raise ValueError("Missing tenantId")

    # Initialize DynamoDB Accessor with your table name
    db_accessor = DynamoDBAccessor(get_table_name())
    return db_accessor.get_all_items_by_tenant(tenant_id)


def handle_rest_request(http_method, tenant_id, section_id, data):
    # Validate input
    if not tenant_id or not section_id:
        raise ValueError("Missing required parameters")

    # Initialize the DynamoDB accessor
    table_name = get_table_name()
    db_accessor = DynamoDBAccessor(table_name)

    # Add 'lastUpdated' to your data
    if data is not None:
        # Get current time as unix time in milliseconds
        now = datetime.datetime.now()
        timestamp = int(now.timestamp() * 1000)
        data['lastUpdated'] = timestamp

    # Handle different HTTP methods
    if http_method == 'GET':
        # Retrieve an item
        item = db_accessor.get_item(tenant_id, section_id)
        if item is not None:
            return item['data']
        else:
            return None

    elif http_method == 'POST':
        # Create a new item is not supported.
        raise ValueError(f"Invalid operation")

    elif http_method == 'PUT':
        # Update an existing item
        return db_accessor.put_item(tenant_id, section_id, data)

    elif http_method == 'DELETE':
        # Delete an item is not supported.
        raise ValueError(f"Invalid operation")

    else:
        raise ValueError(f"Unsupported HTTP method: {http_method}")


# Custom encoder function - TODO: Move to utils to avoid duplicate code
def dynamodb_decimal_default_encoder(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # or use str(obj) if you want to preserve exactness
    raise TypeError
