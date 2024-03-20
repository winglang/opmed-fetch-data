import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests

from proactive_nudge_reminder.send_email import send_email
from utils.jwt_utils import generate_jwt
from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS, get_service

url = os.getenv("URL")


def send_reminder(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event["headers"])

    print(f"username: {username}")

    tenant = get_service(event)
    print(f"tenant: {tenant}")

    request_body = json.loads(event["body"])
    blocks = request_body["blocks"]

    for block in blocks:
        block["doctorName"] = request_body["doctorName"]

    headers = {key: val for key, val in event.get("headers", {}).items() if key.lower() in AUTH_HEADERS}

    recipients = sorted(request_body["recipients"])
    link_for_surgeon = create_link(tenant, blocks, request_body["doctorName"])

    method = event["path"].rsplit("/", 1)[-1]
    if method == "send-email":
        subject = get_email_subject(blocks)
        email = {
            "html": request_body["content"] + f"<br/>please reply in this <a href={link_for_surgeon}>link</a>"
        }
        send_email(subject=subject, body=email, recipients=recipients)
        res = "sent nudge email"
    else:
        res = f"method not found: {method}"

    update_blocks_status(blocks, headers)

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": res}


def get_email_subject(blocks):
    days = [
        datetime.strftime(date, "%b %d, %Y")
        for date in sorted({datetime.fromisoformat(block["start"]) for block in blocks})
    ]
    if len(days) > 1:
        days = ", ".join(days[:-1]) + " and " + days[-1]
    else:
        days = days[0]
    subject = f"Request for Adjusted Surgery Duration on {days}"
    return subject


def create_link(tenant, blocks, user_id):
    block_ids: str = ",".join([block["blockId"] for block in blocks])
    params = {"token": generate_jwt(tenant, user_id, block_ids), "ids": block_ids}

    return url + "/block-release?" + urlencode(params, doseq=True)


def update_blocks_status(blocks, headers):
    for block in blocks:
        block["releaseStatus"] = "pending"
        block["expired_at"] = int(datetime.fromisoformat(block["start"]).timestamp())

    block_ids = [block["blockId"] for block in blocks]
    update_url = f"{url}/api/v1/resources/proactive_blocks_status/bundle"
    requests.put(update_url, json=blocks, params={"ids": block_ids}, headers=headers)
