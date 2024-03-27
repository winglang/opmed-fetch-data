import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests

from proactive_nudge_reminder.send_email import send_email
from utils.jwt_utils import generate_jwt
from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS, get_service

url = os.getenv("URL")
url_surgeon_app = os.getenv("URL_SURGEON_APP")


def send_reminder(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event["headers"])
    hospital_name = event['headers'].get('gmix_serviceid',"Hospital").split("-")[0].upper()



    print(f"username: {username}")

    tenant = get_service(event)
    print(f"tenant: {tenant}")

    request_body = json.loads(event["body"])
    blocks = request_body["blocks"]
    doctor_name = request_body["doctorName"]

    for block in blocks:
        block["doctorName"] = request_body["doctorName"]

    headers = {key: val for key, val in event.get("headers", {}).items() if key.lower() in AUTH_HEADERS}

    recipients = sorted(request_body["recipients"])
    link_for_surgeon = create_link(tenant, blocks, doctor_name)

    method = event["path"].rsplit("/", 1)[-1]
    if method == "send-email":
        subject = f"Request for unused block time release"
        email = {
            "html": "<img src='https://gmix-sync.s3.amazonaws.com/public-items/opmed-logo.png' alt='' />" + request_body["content"] + f"<br/>Dear Dr.{doctor_name}<br/>We hope this message finds you well.<br/><br/>We kindly request your assistance in releasing your block time and providing your approval via the attached link on "
                                              f"<a href={link_for_surgeon}>Opmed.ai</a><br/>"
                                              f"This step is crucial for optimizing our scheduling and ensuring the best use of our resources.<br/>"
                                              f"Thank you for your cooperation and understanding.<br/><br/>"
                                              f"Best regards,<br/>"
                                              f"{hospital_name} Perioperative Leadership Team"
        }
        send_email(subject=subject, body=email, recipients=recipients)
        res = "sent nudge email"
    else:
        res = f"method not found: {method}"

    update_blocks_status(blocks, headers)

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": res}


def create_link(tenant, blocks, user_id):
    block_ids: str = ",".join([block["blockId"] for block in blocks])
    params = {"token": generate_jwt(tenant, user_id, block_ids), "ids": block_ids}

    return url_surgeon_app + "?" + urlencode(params, doseq=True)


def update_blocks_status(blocks, headers):
    for block in blocks:
        block["releaseStatus"] = "pending"
        block["expired_at"] = int(datetime.fromisoformat(block["start"]).timestamp())

    block_ids = [block["blockId"] for block in blocks]
    update_url = f"{url}/api/v1/resources/proactive_blocks_status/bundle"
    requests.put(update_url, json=blocks, params={"ids": block_ids}, headers=headers)
