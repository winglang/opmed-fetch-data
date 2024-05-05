import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests

from proactive_nudge_reminder.flex_blocks_notification import send_flex_blocks_notification
from proactive_nudge_reminder.notification_message_details import NotificationMessage
from proactive_nudge_reminder.proactive_block_release_notification import send_proactive_block_release_notification
from utils.jwt_utils import generate_jwt
from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS, get_service

url_surgeon_app = os.getenv('URL_SURGEON_APP')
url = os.getenv('URL')

nudge_category_to_dv_table_name = {
    'proactive-block-release': 'proactive_blocks_status',
    'flex_blocks': 'flex_blocks_status',
}


def send_reminder(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers'])
    hospital_name = event['headers'].get('gmix_serviceid', 'Hospital').split('-')[0].upper()

    print(f'username: {username}')

    tenant = get_service(event)
    print(f'tenant: {tenant}')

    request_body = json.loads(event['body'])
    blocks = request_body['blocks']
    doctor_name = request_body['doctorName']
    doctor_id = request_body['doctorId']

    for block in blocks:
        block['doctorName'] = doctor_name
        block['doctorId'] = doctor_id

    headers = {key: val for key, val in event.get('headers', {}).items() if key.lower() in AUTH_HEADERS}

    recipients = sorted(request_body['recipients'])
    link_for_surgeon = create_link(tenant, doctor_id)
    nudge_content = request_body.get('content', '')

    path = event['requestContext']['http']['path']

    path_splits = path[1:].split('/')
    nudge_method = path_splits[-1]
    nudge_category = path_splits[-2] if path_splits[-2] != 'nudge-reminder' else 'proactive-block-release'

    if nudge_category not in nudge_category_to_dv_table_name.keys():
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': f'Category not allowed: {nudge_category}',
        }

    print(f'Nudge method is: {nudge_method}')
    print(f'Nudge category is: {nudge_category}')

    notification_message_details = NotificationMessage(
        hospital_name, recipients, nudge_content, doctor_name, link_for_surgeon
    )
    match nudge_category:
        case 'proactive-block-release':
            res = send_proactive_block_release_notification(nudge_method, notification_message_details)
        case 'flex_blocks':
            res = send_flex_blocks_notification(nudge_method, notification_message_details)
        case _:
            res = None

    if isinstance(res, dict):
        return res

    print(f'Sent nudge to {recipients} with method: {nudge_method}')

    block_status_name = nudge_category_to_dv_table_name[nudge_category]

    update_blocks_status(blocks, headers, block_status_name)
    print(f"Updated blocks statuses to pending: {[block["blockId"] for block in blocks]}")

    return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': res}


def create_link(tenant: str, user_id: str) -> str:
    params = {'token': generate_jwt(tenant, user_id)}

    return url_surgeon_app + '?' + urlencode(params, doseq=True)


def update_blocks_status(blocks: list, headers: dict, block_status_name: str) -> None:
    for block in blocks:
        block['releaseStatus'] = 'pending'
        block['expired_at'] = int(datetime.fromisoformat(block['start']).timestamp())

    block_ids = [block['blockId'] for block in blocks]
    update_url = f'{url}/api/v1/resources/{block_status_name}/bundle'
    requests.put(update_url, json=blocks, params={'ids': block_ids}, headers=headers)
