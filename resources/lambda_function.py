import datetime
import json
import os
from decimal import Decimal

from utils.dynamodb_accessor import DynamoDBAccessor
from utils.hash_utils import generate_sha256_hash
from utils.services_utils import get_service, handle_error_response, lowercase_headers, get_username, \
    create_error_response, valid_service

SALT = os.getenv('HASH_ID_SALT')


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

    # get the resource category.
    path_splits = path.split('/')
    if len(path_splits) not in [5, 6]:
        print("Invalid URL path length.")
        return create_error_response(400, 'Invalid request')

    # We handle only specific categories.
    valid_categories = ["surgeons", "nurses", "anesthesiologists", "proactive_blocks_status"]
    resource_category_id = path_splits[4]
    if resource_category_id not in valid_categories:
        print(
            f"Invalid requests. resource_category_id: {resource_category_id} was given. Valid categories: {valid_categories}")
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
        query_string_parameters = event.get('queryStringParameters', {})
        resource_ids = query_string_parameters.get('ids').split(',') if 'ids' in query_string_parameters else []

        if path_splits[5] == 'bundle':
            if not resource_ids:
                print("Invalid request. Requests bundle but didn't provide ids")
                return create_error_response(400, 'Invalid request')
        else:
            if resource_ids:
                print("Invalid request. Provide multiple ids but didn't request bundle")
                return create_error_response(400, 'Invalid request')
            resource_ids = [path_splits[5]]

        data_object = None
        if event is not None and "body" in event and event["body"] is not None:
            data_object = json.loads(event['body'])
        if type(data_object) is dict:
            data_object = [data_object]

        if http_method in ['POST', 'PUT', 'PATCH']:
            if len(resource_ids) != len(data_object):
                print(
                    f"Invalid request. Mismatch between resource_ids and data_object. "
                    f"Requested {len(resource_ids)} ids but sent {len(data_object)} objects")
                create_error_response(400, 'Invalid request')
        try:
            if resource_ids == ["filterByField"]:
                data_object = username
            result = handle_rest_request(http_method, service, resource_category_id, resource_ids, data_object)
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


def handle_mapping_request(items_to_hash):
    return [generate_sha256_hash(item, salt=SALT) for item in items_to_hash]


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


def handle_rest_request(http_method, tenant_id, category_id, resource_ids, data):
    # Validate input
    if not tenant_id or not category_id or not resource_ids:
        raise ValueError("Missing required parameters")

    if resource_ids == ["mapping"]:
        return handle_mapping_request(data)

    # Initialize the DynamoDB accessor
    table_name = get_table_name(category_id)
    db_accessor = DynamoDBAccessor(table_name)
    internal_to_external_ids_table = os.environ['internal_to_external_ids']

    metadata = {}
    if data is not None and resource_ids != ["filterByField"]:
        # Get current time as unix time in milliseconds
        now = datetime.datetime.now()
        timestamp = int(now.timestamp() * 1000)
        metadata['lastUpdated'] = timestamp

    # Handle different HTTP methods
    if http_method == 'GET':
        if resource_ids == ["filterByField"]:
            items = db_accessor.filter_by_field(tenant_id, "doctorId", data)
        else:
            # Retrieve an item
            items = db_accessor.batch_get_item(tenant_id, resource_ids)
        if items:
            items = [item.get('data', item) for item in items]
            return items[0] if len(items) == 1 else items
        else:
            return None

    elif http_method == 'POST':
        # Create a new item
        # check that object does not exist before adding.
        categories_with_hash_id = ["surgeons", 'proactive_blocks_status']
        internal_resource_ids = [generate_sha256_hash(
            resource_id, SALT) for resource_id in
            resource_ids] if category_id in categories_with_hash_id else resource_ids
        ids_db_accessor = DynamoDBAccessor(internal_to_external_ids_table)
        items = ids_db_accessor.batch_get_item(tenant_id, internal_resource_ids)
        if items:
            raise FileExistsError(f"Resource already exist: {internal_resource_ids}")
        # store internal id. TODO: Transaction
        id_created = ids_db_accessor.batch_put_item(tenant_id, internal_resource_ids, resource_ids)
        if id_created is False:
            raise ValueError(f"Fail to create internal id for external id. {internal_resource_ids}")

        for internal_resource_id, data_item in zip(internal_resource_ids, data):
            data_item['id'] = internal_resource_id

        categories_saved_nested = ["surgeons", "nurses", "anesthesiologists"]
        save_nested = category_id in categories_saved_nested
        if len(resource_ids) == 1:
            return db_accessor.put_item(tenant_id, resource_ids[0], data[0], save_nested=save_nested, metadata=metadata)
        return db_accessor.batch_put_item(tenant_id, internal_resource_ids, data, save_nested=save_nested,
                                          metadata=metadata)

    elif http_method == 'PUT':
        # Update an existing item
        categories_saved_nested = ["surgeons", "nurses", "anesthesiologists"]
        save_nested = category_id in categories_saved_nested
        if len(resource_ids) == 1:
            return db_accessor.put_item(tenant_id, resource_ids[0], data[0], save_nested=save_nested, metadata=metadata)
        return db_accessor.batch_put_item(tenant_id, resource_ids, data, save_nested=save_nested, metadata=metadata)

    elif http_method == 'PATCH':
        allowed_categories = ["proactive_blocks_status"]
        if category_id not in allowed_categories:
            raise ValueError(f"Unsupported category for PATCH: {category_id}")
        if len(resource_ids) == 1:
            return db_accessor.update_item(tenant_id, resource_ids[0], data[0])
        return db_accessor.batch_update_item(tenant_id, resource_ids, data)

    elif http_method == 'DELETE':
        # Delete an item
        ids_db_accessor = DynamoDBAccessor(internal_to_external_ids_table)
        id_deleted = ids_db_accessor.batch_delete_item(tenant_id, resource_ids)
        if id_deleted is False:
            raise ValueError(f"Fail to delete internal id for external id. {resource_ids}")
        if len(resource_ids) == 1:
            return db_accessor.delete_item(tenant_id, resource_ids[0])
        return db_accessor.batch_delete_item(tenant_id, resource_ids) is not None

    else:
        raise ValueError(f"Unsupported HTTP method: {http_method}")


# Custom encoder function - TODO: Move to utils to avoid duplicate code
def dynamodb_decimal_default_encoder(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # or use str(obj) if you want to preserve exactness
    raise TypeError
