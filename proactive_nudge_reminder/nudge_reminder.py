import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests

from proactive_nudge_reminder.proactive_block_release_notification import send_proactive_block_release_notification
from utils.jwt_utils import generate_jwt
from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS, get_service

url = os.getenv('URL')
url_surgeon_app = os.getenv('URL_SURGEON_APP')

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

    path_splits = event['path'].rsplit('/', maxsplit=2)
    nudge_method = path_splits[-1]
    nudge_category = path_splits[-2] if path_splits[-2] != 'nudge_reminder' else 'proactive-block-release'

    if nudge_category not in nudge_category_to_dv_table_name.keys():
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': f'Category not allowed: {nudge_category}',
        }

    print(f'Nudge method is: {nudge_method}')
    print(f'Nudge category is: {nudge_category}')

    match nudge_category:
        case 'proactive-block-release':
            send_proactive_block_release_notification(
                nudge_method, hospital_name, recipients, nudge_content, doctor_name, link_for_surgeon
            )
        case 'flex_blocks':
            pass

    print(f'Sent nudge to {recipients} with method: {nudge_method}')

    block_status_name = nudge_category_to_dv_table_name[nudge_category]
    update_blocks_status(blocks, headers, block_status_name)
    print(f"Updated blocks statuses to pending: {[block["blockId"] for block in blocks]}")

    return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': res}


def get_email_content(content: str, doctor_name: str, link: str, hospital_name: str) -> str:
    return (
        f"<img src='https://gmix-sync.s3.amazonaws.com/public-items/opmed-logo.png' alt='' />{content}"
        f'<br/>Dear Dr.{doctor_name}<br/>We hope this message finds you well.<br/><br/>We kindly request your assistance in releasing your block time and providing your approval via the '
        f'attached <a href={link}>link</a> on Opmed.ai <br/>'
        f'This step is crucial for optimizing our scheduling and ensuring the best use of our resources.<br/>'
        f'Thank you for your cooperation and understanding.<br/><br/>'
        f'Best regards,<br/>'
        f'{hospital_name} Perioperative Leadership Team'
    )


def get_sms_content(doctor_name: str, link: str, hospital_name: str) -> str:
    return (
        f'Dear Dr.{doctor_name}, We hope this message finds you well. We kindly request your assistance in releasing your block time and providing your approval via this link '
        f'{link} on Opmed.ai\n'
        f'This step is crucial for optimizing our scheduling and ensuring the best use of our resources\n'
        f'Thank you for your cooperation and understanding.\n'
        f'Best regards,\n'
        f'{hospital_name} Perioperative Leadership Team.'
    )


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
