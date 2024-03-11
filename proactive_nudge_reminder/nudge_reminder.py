import json
import os
import urllib
from datetime import datetime

import requests

from proactive_nudge_reminder.send_email import send_email
from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS

url = os.getenv('URL')


def send_reminder(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    request_body = json.loads(event['body'])
    blocks = request_body['blocks']

    queryStringParameters = {key: val for key, val in event.get('queryStringParameters', {}).items() if
                             key in ['from', 'to']}
    headers = {key: val for key, val in event.get('headers', {}).items() if
               key.lower() in AUTH_HEADERS}

    update_blocks_status(blocks, headers, queryStringParameters)

    link_for_surgeon = create_link(blocks)

    method = event['path'].rsplit('/', 1)[-1]
    if method == 'send-email':
        days = [datetime.strftime(date, "%b %d, %Y") for date in
                sorted({datetime.fromisoformat(block['start']) for block in blocks})]
        if len(days) > 1:
            days = ', '.join(days[:-1]) + ' and ' + days[-1]
        else:
            days = days[0]
        subject = f'Request for Adjusted Surgery Duration on {days}'
        email_text = request_body['content'] + '\n\n' + f'please reply in the provided link\n\n{link_for_surgeon}'
        send_email(subject=subject, body={'text': email_text}, recipients=request_body['recipients'])
        res = 'sent nudge email'
    else:
        res = f'method not found: {method}'

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": res
    }


def generate_token():
    return 'temp_token'


def create_link(blocks):
    params = {
        'token': generate_token(),
        'block_ids': [block['blockId'] for block in blocks]
    }

    return url + '/block-release?' + urllib.parse.urlencode(params)


def update_blocks_status(blocks, headers, queryStringParameters):
    for block in blocks:
        block['releaseStatus'] = 'pending'
        block['expired_at'] = int(datetime.fromisoformat(block['start']).timestamp())
        update_url = f'{url}/api/v1/resources/proactive_blocks_status/{block['blockId']}'

        requests.put(update_url, json=block, headers=headers, params=queryStringParameters)
