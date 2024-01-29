import datetime
import json
import os
from decimal import Decimal

import hashlib
from utils.dynamodb_accessor import DynamoDBAccessor
from utils.services_utils import get_service, handle_error_response, lowercase_headers, get_username, \
    create_error_response, valid_service


def lambda_handler(event, context):
    print(event)

    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    for key in event:
        print(key)

    service = get_service(event)
    if not valid_service(service):
        return handle_error_response(service)

    # Extracting HTTP method and path from the event
    http_method = event['requestContext']['http']['method']
    path = event['requestContext']['http']['path']

    if not path.startswith('/api/v1/resources'):
        print("Invalid path.")
        return create_error_response(400, 'Invalid request')

    # get the resource category.
    path_splits = path.split('/')
    if len(path_splits) not in [5, 6]:
        print("Invalid URL path length.")
        return create_error_response(400, 'Invalid request')

    # We handle only specific categories.
    valid_categories = ["surgeons", "nurses", "anesthesiologists"]
    resource_category_id = path_splits[4]
    if resource_category_id not in valid_categories:
        return create_error_response(400, 'Invalid request')

    # Check if the method is GET and the path is /api/v1/resources/<category_id> - list all objects.
    if http_method == 'GET' and len(path_splits) == 5:
        all_data = get_all_data_for_category(service, resource_category_id)
        print("Read all data. len:", len(all_data))
        return {
            'statusCode': 200,
            "headers": {
                "Content-Type": "application/json"
            },
            'body': json.dumps(all_data, default=dynamodb_decimal_default_encoder)
        }

    else:  # For other cases, perform "rest" operations with the resource id.
        resource_id = path_splits[5]
        data_object = None
        if event is not None and "body" in event and event["body"] is not None:
            data_object = json.loads(event['body'])
        try:
            result = handle_rest_request(http_method, service, resource_category_id, resource_id, data_object)
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
        except FileExistsError as e2:
            print(f"Caught an error: {e2}")
            return create_error_response(409, 'Already exists')


def get_table_name(category_id):
    table_name = os.getenv(category_id)
    if table_name is None or table_name == "":
        raise ValueError("Missing category. " + str(category_id))
    return table_name


def get_all_data_for_category(tenant_id, category_id):
    # Ensure that tenant_id is provided
    if not tenant_id:
        raise ValueError("Missing tenantId")

    table_name = get_table_name(category_id)

    # Initialize DynamoDB Accessor with your table name
    db_accessor = DynamoDBAccessor(table_name)

    # Retrieve all records for the given tenant
    # TODO: add pagination.
    items = db_accessor.list_items_by_tenant(tenant_id)
    return items


def handle_rest_request(http_method, tenant_id, category_id, resource_id, data):
    # Validate input
    if not tenant_id or not category_id or not resource_id:
        raise ValueError("Missing required parameters")

    # Initialize the DynamoDB accessor
    table_name = get_table_name(category_id)
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
        item = db_accessor.get_item(tenant_id, resource_id)
        if item is not None:
            return item['data']
        else:
            return None

    elif http_method == 'POST':
        # Create a new item
        # check that object does not exist before adding.
        categories_with_hash_id = ["surgeons"]
        slat = os.environ['HASH_ID_SALT']
        internal_resource_id = generate_sha256_hash(resource_id,
                                                    slat) if category_id in categories_with_hash_id else resource_id
        item = db_accessor.get_item(tenant_id, internal_resource_id)
        if item is not None:
            raise FileExistsError(f"Resource already exist: {internal_resource_id}")
        # store internal id. TODO: Transaction
        ids_db_accessor = DynamoDBAccessor('internal-to-external-ids')
        id_created = ids_db_accessor.put_item(tenant_id, internal_resource_id, resource_id)
        if id_created is False:
            raise ValueError(f"Fail to create internal id for external id. {internal_resource_id}")
        data['id'] = internal_resource_id
        return db_accessor.put_item(tenant_id, internal_resource_id, data)

    elif http_method == 'PUT':
        # Update an existing item
        return db_accessor.put_item(tenant_id, resource_id, data)

    elif http_method == 'DELETE':
        # Delete an item
        ids_db_accessor = DynamoDBAccessor('internal-to-external-ids')
        id_deleted = ids_db_accessor.delete_item(tenant_id, resource_id)
        if id_deleted is False:
            raise ValueError(f"Fail to delete internal id for external id. {resource_id}")
        return db_accessor.delete_item(tenant_id, resource_id) is not None

    else:
        raise ValueError(f"Unsupported HTTP method: {http_method}")


# Custom encoder function - TODO: Move to utils to avoid duplicate code
def dynamodb_decimal_default_encoder(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # or use str(obj) if you want to preserve exactness
    raise TypeError


def generate_sha256_hash(data, salt):
    data_with_salt = data + salt
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data_with_salt.encode())
    hashed_string = sha256_hash.hexdigest()
    return hashed_string
