import json
import os
from concurrent.futures import ThreadPoolExecutor

from flex_blocks.get_potential_flex_blocks import get_potential_flex_blocks
from utils.api_utils import invoke_fetch_data, fetch_default_to_value, fetch_default_from_value
from utils.dynamodb_accessor import get_blocks_status
from utils.encoders import GeneralEncoder
from utils.s3_utils import store_s3_with_acl
from utils.services_utils import lowercase_headers, get_username, get_service

json_file_name = os.getenv('JSON_FILE_NAME')
blocks_status_table_name = os.getenv('BLOCKS_STATUS_TABLE_NAME')

DB_FIELDS_PROJECTION = {'data_id', 'lastUpdated', 'blockStatus'}


def flex_block_handler(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers'])

    print(f'username: {username}')

    tenant = get_service(event)
    print(f'tenant: {tenant}')

    queryStringParameters = event.get('queryStringParameters', {})
    print(f'queryStringParameters: {queryStringParameters}')

    queryStringParameters['from'] = queryStringParameters.get('from', fetch_default_from_value())
    queryStringParameters['to'] = queryStringParameters.get('to', fetch_default_to_value())

    headers_for_identification = {'user-id': username, 'tenant-id': tenant}
    fetch_data = invoke_fetch_data(queryStringParameters, headers_for_identification)

    for task in fetch_data['tasks']:
        if 'start' in task:
            task['start_time'] = task.pop('start')
        if 'end' in task:
            task['end_time'] = task.pop('end')
        if 'resources_ids' in task:
            task['resources'] = task.pop('resources_ids')

    with ThreadPoolExecutor() as executor:
        get_potential_flex_blocks_future = executor.submit(
            get_potential_flex_blocks, fetch_data, headers_for_identification
        )
        get_blocks_status_future = executor.submit(
            get_blocks_status,
            queryStringParameters['from'],
            queryStringParameters['to'],
            tenant,
            blocks_status_table_name,
            DB_FIELDS_PROJECTION,
        )

        flex_blocks_res = get_potential_flex_blocks_future.result()
        blocks_status_res = get_blocks_status_future.result()

    if flex_blocks_res['statusCode'] == 200:
        flex_blocks = flex_blocks_res['body']
        for block_id, block in flex_blocks.items():
            flex_blocks[block_id] |= blocks_status_res.get(block_id, {'blockStatus': 'new'})
        response_body = json.dumps(flex_blocks, cls=GeneralEncoder, sort_keys=True)
    else:
        response_body = flex_blocks_res['error']
    save_to_s3 = (event.get('queryStringParameters') or {}).get('save_to_s3', False)
    if save_to_s3:
        s3_key = os.path.join(tenant, json_file_name)
        bucket_name = os.environ['BUCKET_NAME']
        store_s3_with_acl(bucket_name, s3_key, response_body)

    return {
        'statusCode': flex_blocks_res['statusCode'],
        'headers': {'Content-Type': 'application/json'},
        'body': response_body,
    }
