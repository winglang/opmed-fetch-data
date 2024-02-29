import json
import os
import re
from datetime import datetime
import time

import requests

from utils.services_utils import lowercase_headers, get_username

# TODO: modify prompt to explain differences between alternative_plans and original_schedule

api_key = os.getenv('API_KEY')
lang_model_url = os.getenv('LANG_MODEL_URL')


def compute_differences(plans):
    alternative_plan_blocks = {block['id']: block for block in plans['alternative_plan']['blocks']}
    original_plan_blocks = {block['id']: block for block in plans['original_plan']['blocks']}
    changes_scores = [score_block_difference(block, alternative_plan_blocks[block_id]) for block_id, block in
                      original_plan_blocks.items() if block_id in alternative_plan_blocks]
    changes_scores.sort(key=lambda x: x['score'], reverse=True)
    return changes_scores


def explain_alternative_plans(plans):
    changes_scores = compute_differences(plans)

    num_differences_to_display = 3
    changes_to_display = changes_scores[:num_differences_to_display]
    # TODO: make the decoding and encoding work for future query types
    doctor_names = ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown', 'Dr. Jones', 'Dr. Miller', 'Dr. Davis',]
    mapping = {change['surgeon']: doctor_name for change, doctor_name in zip(changes_to_display, doctor_names)}
    for change in changes_to_display:
        change.pop('score')
        change['surgeon'] = mapping[change['surgeon']]
    reversed_mapping = {v: f'<{k}>' for k, v in mapping.items()}


    print("asking lang model")

    return (
        f"Given a daily OR schedule, we have computed an alternative schedule."
        f"Specifically, we have changed the room, start time and duration of some blocks."
        f"The biggest block differences between the original and alternative schedules are: {changes_to_display}"
        f"Concisely explain these differences to an OR scheduler."
        f"Do not use the word slot. "
        f"To describe a block, use the name of the surgeon, the room and the start time."
        f"Do not provide introduction, just list the changes."

    ), reversed_mapping











def query_lang_model(content):
    request = {
        "messages": [
            {
                "role": "system",
                "content": content
            }
        ],
        "temperature": 0.9,
        "top_p": 0.95, # sample from the top 95% of the distribution
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
    start_time = time.time()  # Record the start time
    method = event['path'].rsplit('/', 1)[-1]
    if method == 'explain-alternative-plans':
        prompt, name_mapping = explain_alternative_plans(event['body'])
        res = query_lang_model(prompt)
        pattern = re.compile("|".join(name_mapping.keys()))
        res = pattern.sub(lambda m: name_mapping[re.escape(m.group(0)).replace('\\', '')], res)
    elif method == 'explain-block-allocation':
        res = query_lang_model(explain_alternative_plans(event['body']))
    else:
        res = f'method not found: {method}'


    end_time = time.time()  # Record the end time

    print(f"chatGPT query time: {end_time - start_time} seconds.")


    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": res
    }


def score_block_difference(original_block, alternative_block):

    original_block['start'] = datetime.fromisoformat(original_block['start'])
    original_block['end'] = datetime.fromisoformat(original_block['end'])

    alternative_block['start'] = datetime.fromisoformat(alternative_block['start'])
    alternative_block['end'] = datetime.fromisoformat(alternative_block['end'])

    original_block_duration = (original_block['end'] - original_block['start']).total_seconds() / 3600
    alternative_block_duration = (alternative_block['end'] - alternative_block['start']).total_seconds() / 3600

    is_room_changed = original_block['resourceId'] != alternative_block['resourceId']

    start_time_change = abs((alternative_block['start'] - original_block['start']).total_seconds() / 3600)
    start_time_change = start_time_change if start_time_change >= 0.5 else 0

    duration_change = abs(alternative_block_duration - original_block_duration)
    duration_change = duration_change if duration_change >= 0.5 else 0



    c1, c2, c3 = 1, 1, 2
    return {
        'surgeon': original_block['doctor_id'],
        'original_room': original_block['resourceId'],
        'original_start': original_block['start'].time(),
        'alternative_room': alternative_block['resourceId'],
        'alternative_start': alternative_block['start'].time(),
        'original_duration': original_block_duration,
        'alternative_block_duration': alternative_block_duration,

        # 'is_room_changed': is_room_changed,
        # 'start_time_change': start_time_change,
        # 'duration_change': duration_change,
         'score': original_block_duration * (c1 * is_room_changed + c2 * start_time_change + c3 * duration_change),
    }













