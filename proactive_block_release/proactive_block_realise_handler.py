import decimal
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Key, Attr

from utils.lambda_utils import invoke_lambda_function
from utils.services_utils import lowercase_headers, get_username, get_service

fetch_data_lambda_name = os.getenv('FETCH_DATA_LAMBDA_NAME')
predict_blocks_lambda_name = os.getenv('PREDICT_BLOCKS_LAMBDA_NAME')
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
        KeyConditionExpression=Key('tenant_id').eq(tenant),
        FilterExpression=Attr('start').between(start, end)
    )

    return {block['data_id']: {k: v for k, v in block.items() if k in BLOCK_FIELDS_TO_RETURN} for block in
            response['Items']}


def get_blocks_predictions(fetch_data, headers):
    data_to_predict = {
        'blocks': fetch_data["blocks"],
        'tasks': fetch_data["tasks"],
        "metadata": {
            "use_ai_predictions": True,
            "min_task_pred_abs": 15,
            "min_task_pred_percent": 0,
            "min_block_pred_abs": 0,
            "min_block_pred_percent": 0,
            "ignored_tasks_list": [],
            "ignored_blocks_list": []
        }
    }

    event = {
        'headers': headers,
        'path': 'invoked_by_proactive_block_release/algo/block-population-risk',
        'body': json.dumps(data_to_predict)
    }

    try:
        predict_blocks_res = invoke_lambda_function(predict_blocks_lambda_name, event)
    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e)
        }
    return {
        "statusCode": 200,
        "body": predict_blocks_res['blocks']
    }


def invoke_fetch_data(query_string_parameters, headers):
    default_from_value = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')  # Today + 3 days
    default_to_value = (datetime.now() + timedelta(days=31)).strftime('%Y-%m-%d')  # Today + 31 days

    query_string_parameters = {key: val for key, val in query_string_parameters.items() if key in ['from', 'to']}
    query_string_parameters['from'] = query_string_parameters.get('from', default_from_value)
    query_string_parameters['to'] = query_string_parameters.get('to', default_to_value)
    event = {
        "queryStringParameters": query_string_parameters,
        'headers': headers,
        'path': '/fetch-data/v2'
    }

    return invoke_lambda_function(fetch_data_lambda_name, event)


def proactive_block_realise_handler(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers'])

    print(f'username: {username}')

    tenant = get_service(event)
    print(f'tenant: {tenant}')

    queryStringParameters = event.get('queryStringParameters', {})
    print(f'queryStringParameters: {queryStringParameters}')

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
        get_blocks_status_future = executor.submit(get_blocks_status, queryStringParameters['from'],
                                                   queryStringParameters['to'], tenant)

        blocks_predictions_res = get_blocks_predictions_future.result()
        blocks_status = get_blocks_status_future.result()

    if blocks_predictions_res['statusCode'] == 200:
        predicted_blocks = blocks_predictions_res['body']
        for block in predicted_blocks:
            block |= blocks_status.get(block['id'], {'releaseStatus': 'new'})
        response_body = json.dumps(predicted_blocks, cls=DecimalEncoder)
    else:
        response_body = blocks_predictions_res['error']
    save_to_s3 = (event.get("body") or {}).get("save_to_s3", False)
    if save_to_s3:
        s3_key = "proactive-block.json"
        bucket_name = os.environ['BUCKET_NAME']
        try:
            s3 = boto3.resource('s3')
            s3object = s3.Object(bucket_name, s3_key)
            s3object.put(
                Body=response_body
            )
            s3.put_object_acl(
                Bucket=bucket_name,
                Key=s3_key,
                ACL='authenticated-read'
            )
            print("Success: Saved to S3")
        except Exception as e:
            print("Error: {}".format(e))

    return {
        "statusCode": blocks_predictions_res['statusCode'],
        "headers": {
            "Content-Type": "application/json"
        },
        "body": response_body
    }
