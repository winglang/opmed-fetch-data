import json
import os

import requests

from utils.services_utils import lowercase_headers, get_username

# TODO: modify prompt to explain differences between alternative_plans and original_schedule

api_key = os.getenv('API_KEY')
lang_model_url = os.getenv('LANG_MODEL_URL')


def explain_alternative_plans(plans):
    return (
        f"Given as stringified json, what are the 5 major differences between alternative_plans and original_schedule. "
        f"Key differences would be the largest blocks that were changed from original plan. "
        f"json is {json.dumps(plans)}. "
        f"Explain as a SAAS platform would explain to an OR scheduler. ֿ"
        f"the plaform takes an original schedule and offers an optimized alternative plan that should improve desired metrics such as cost and utilization. "
        f"Don't use the word JSON in your response. "
        f"alternative plan should have higher utilization and potential revenue. "
        f"decreasing the cost as much as possible is desired"
    )


def query_lang_model(content):
    request = {
        "messages": [
            {
                "role": "system",
                "content": content
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "max_tokens": 800,
        "stop": None
    }
    headers = {'api-key': api_key, 'Content-Type': 'application/json'}
    res = requests.post(lang_model_url, json=request, headers=headers, timeout=600)
    return res.json()['choices'][0]['message']['content']


def query_copilot_lambda_handler(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    method = event['path'].rsplit('/', 1)[-1]
    if method == 'explain-alternative-plans':
        res = query_lang_model(explain_alternative_plans(event['body']))
    elif method == 'explain-block-allocation':
        res = query_lang_model(explain_alternative_plans(event['body']))
    else:
        res = f'method not found: {method}'

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": res
    }
