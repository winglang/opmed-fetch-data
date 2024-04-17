import json
import os

from utils.lambda_utils import invoke_lambda_function

fetch_data_lambda_name = os.getenv('FETCH_DATA_LAMBDA_NAME')
predict_blocks_lambda_name = os.getenv('PREDICT_BLOCKS_LAMBDA_NAME')


def get_blocks_predictions(fetch_data, headers):
    data_to_predict = {
        'blocks': fetch_data['blocks'],
        'tasks': fetch_data['tasks'],
        'metadata': {
            'use_ai_predictions': True,
            'min_task_pred_abs': 15,
            'min_task_pred_percent': 0,
            'min_block_pred_abs': 0,
            'min_block_pred_percent': 0,
            'ignored_tasks_list': [],
            'ignored_blocks_list': [],
        },
    }

    event = {
        'headers': headers,
        'path': 'invoked_by_proactive_block_release/algo/block-population-risk',
        'body': json.dumps(data_to_predict),
    }

    try:
        predict_blocks_res = invoke_lambda_function(predict_blocks_lambda_name, event)
    except Exception as e:
        return {'statusCode': 500, 'error': str(e)}
    return {'statusCode': 200, 'body': predict_blocks_res['blocks']}


def invoke_fetch_data(query_string_parameters, headers):
    query_string_parameters = {key: val for key, val in query_string_parameters.items() if key in ['from', 'to']}

    event = {'queryStringParameters': query_string_parameters, 'headers': headers, 'path': '/fetch-data/v2'}

    return invoke_lambda_function(fetch_data_lambda_name, event)
