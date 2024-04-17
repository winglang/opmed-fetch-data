import decimal
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Key, Attr

from utils.api_utils import invoke_fetch_data, get_blocks_predictions
from utils.services_utils import lowercase_headers, get_username, get_service

json_file_name = os.getenv('JSON_FILE_NAME')
blocks_status_table_name = os.getenv('BLOCKS_STATUS_TABLE_NAME')

BLOCK_FIELDS_TO_RETURN = ['lastUpdated', 'releaseStatus', 'acceptedMinutesToRelease']


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super().default(o)


def get_blocks_status(start, end, tenant):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(blocks_status_table_name)

    response = table.query(
        KeyConditionExpression=Key('tenant_id').eq(tenant), FilterExpression=Attr('start').between(start, end)
    )

    return {
        block['data_id']: {k: v for k, v in block.items() if k in BLOCK_FIELDS_TO_RETURN}
        for block in response['Items']  # TODO use projection expression
    }


def proactive_block_realise_handler(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers'])

    print(f'username: {username}')

    tenant = get_service(event)
    print(f'tenant: {tenant}')

    queryStringParameters = event.get('queryStringParameters', {})
    print(f'queryStringParameters: {queryStringParameters}')

    default_from_value = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')  # Today + 3 days
    default_to_value = (datetime.now() + timedelta(days=31)).strftime('%Y-%m-%d')  # Today + 31 days
    queryStringParameters['from'] = queryStringParameters.get('from', default_from_value)
    queryStringParameters['to'] = queryStringParameters.get('to', default_to_value)

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
        get_blocks_predictions_future = executor.submit(get_blocks_predictions, fetch_data, headers_for_identification)
        get_blocks_status_future = executor.submit(
            get_blocks_status, queryStringParameters['from'], queryStringParameters['to'], tenant
        )

        blocks_predictions_res = get_blocks_predictions_future.result()
        blocks_status = get_blocks_status_future.result()

    if blocks_predictions_res['statusCode'] == 200:
        predicted_blocks = blocks_predictions_res['body']
        for block in predicted_blocks:
            block |= blocks_status.get(block['id'], {'releaseStatus': 'new'})
        response_body = json.dumps(predicted_blocks, cls=DecimalEncoder)
    else:
        response_body = blocks_predictions_res['error']
    save_to_s3 = (event.get('queryStringParameters') or {}).get('save_to_s3', False)
    if save_to_s3:
        s3_key = os.path.join(tenant, json_file_name)
        bucket_name = os.environ['BUCKET_NAME']
        try:
            s3 = boto3.client('s3')

            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=json.dumps(response_body))

            s3.put_object_acl(Bucket=bucket_name, Key=s3_key, ACL='authenticated-read')

            print('Success: Saved to S3')
        except Exception as e:
            print('Error: {}'.format(e))

    return {
        'statusCode': blocks_predictions_res['statusCode'],
        'headers': {'Content-Type': 'application/json'},
        'body': response_body,
    }
