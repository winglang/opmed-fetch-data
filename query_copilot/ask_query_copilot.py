import json
import os
import re
import time
from datetime import datetime

import json_fingerprint
import requests
from json_fingerprint import hash_functions

from query_copilot.constants import TEMPERATURE, TOP_P, FREQUENCY_PENALTY, PRESENCE_PENALTY, MAX_TOKENS, GPT_STOP, \
    NUM_DIFFERENCES_TO_DISPLAY, W_TIME_CHANGE, W_ROOM_CHANGE, W_DURATION_CHANGE
from utils.services_utils import lowercase_headers, get_username

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

    num_differences_to_display = NUM_DIFFERENCES_TO_DISPLAY
    changes_to_display = changes_scores[:num_differences_to_display]
    # TODO: make the decoding and encoding work for future query types
    doctor_names = ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown', 'Dr. Jones', 'Dr. Miller', 'Dr. Davis', ]
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
        f"display numbers in hours and minutes."

    ), reversed_mapping


def query_lang_model(content):
    request = {
        "messages": [
            {
                "role": "system",
                "content": content
            }
        ],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,  # sample from the top 95% of the distribution
        "frequency_penalty": FREQUENCY_PENALTY,
        "presence_penalty": PRESENCE_PENALTY,
        "max_tokens": MAX_TOKENS,
        "stop": GPT_STOP,
    }
    headers = {'api-key': api_key, 'Content-Type': 'application/json'}

    hashed_event = json_fingerprint.create(input=request | headers | lang_model_url,
                                           hash_function=hash_functions.SHA256, version=1)

    res = requests.post(lang_model_url, json=request, headers=headers, timeout=600)
    return res.json()['choices'][0]['message']['content']


def query_copilot_lambda_handler(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    request_data = json.loads(event['body'])

    print(f'username: {username}')
    start_time = time.time()  # Record the start time
    method = event['path'].rsplit('/', 1)[-1]
    if method == 'explain-alternative-plans':
        prompt, name_mapping = explain_alternative_plans(request_data)
        res = query_lang_model(prompt)
        pattern = re.compile("|".join(name_mapping.keys()))
        res = pattern.sub(lambda m: name_mapping[re.escape(m.group(0)).replace('\\', '')], res)
    elif method == 'explain-block-allocation':
        res = query_lang_model(explain_alternative_plans(request_data))
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

    original_start_time_string_am_pm = original_block['start'].strftime("%I:%M %p")
    alternative_start_time_string_am_pm = alternative_block['start'].strftime("%I:%M %p")

    duration_change = abs(alternative_block_duration - original_block_duration)
    duration_change = duration_change if duration_change >= 0.5 else 0

    original_room_number = original_block['resourceId']
    alternative_room_number = alternative_block['resourceId']

    return {
        'surgeon': original_block['doctor_id'],
        'original_room': original_room_number,
        'original_start': original_start_time_string_am_pm,
        'alternative_room': alternative_room_number,
        'alternative_start': alternative_start_time_string_am_pm,
        'original_duration': original_block_duration,
        'alternative_block_duration': alternative_block_duration,
        # 'is_room_changed': is_room_changed,
        # 'start_time_change': start_time_change,
        # 'duration_change': duration_change,
        'score': original_block_duration * (
                W_ROOM_CHANGE * is_room_changed + W_TIME_CHANGE * start_time_change + W_DURATION_CHANGE * duration_change),
    }
