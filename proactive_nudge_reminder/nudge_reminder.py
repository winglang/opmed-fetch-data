import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests

from utils.jwt_utils import generate_jwt
from utils.send_notification.send_email import send_email
from utils.send_notification.send_sms import send_sms
from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS, get_service

url = os.getenv("URL")
url_surgeon_app = os.getenv("URL_SURGEON_APP")


def send_reminder(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event["headers"])
    hospital_name = event['headers'].get('gmix_serviceid', "Hospital").split("-")[0].upper()

    print(f"username: {username}")

    tenant = get_service(event)
    print(f"tenant: {tenant}")

    request_body = json.loads(event["body"])
    blocks = request_body["blocks"]
    doctor_name = request_body["doctorName"]
    doctor_id = request_body["doctorId"]

    for block in blocks:
        block["doctorName"] = doctor_name
        block["doctorId"] = doctor_id

    headers = {key: val for key, val in event.get("headers", {}).items() if key.lower() in AUTH_HEADERS}

    recipients = sorted(request_body["recipients"])
    link_for_surgeon = create_link(tenant, blocks, doctor_id)
    nudge_content = request_body["content"]

    method = event["path"].rsplit("/", 1)[-1]
    match method:
        case "send-email":
            subject = f"Request for unused block time release"
            email = {
                "html": get_email_content(nudge_content, doctor_name, link_for_surgeon, hospital_name)
            }
            send_email(subject=subject, body=email, recipients=recipients)
            res = "Sent nudge email"
        case "send-sms":
            sms_txt = get_sms_content(nudge_content, doctor_name, link_for_surgeon, hospital_name)
            send_sms(recipients[0], sms_txt, sender_id=hospital_name)
            res = "Sent nudge sms"

        case _:
            return {"statusCode": 400, "headers": {"Content-Type": "application/json"},
                    "body": f"Method not found: {method}"}

    update_blocks_status(blocks, headers)

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": res}


def get_email_content(content, doctor_name, link, hospital_name):
    return (
        f"<img src='https://gmix-sync.s3.amazonaws.com/public-items/opmed-logo.png' alt='' />{content}"
        f"<br/>Dear Dr.{doctor_name}<br/>We hope this message finds you well.<br/><br/>We kindly request your assistance in releasing your block time and providing your approval via the "
        f"attached <a href={link}>link</a> on Opmed.ai <br/>"
        f"This step is crucial for optimizing our scheduling and ensuring the best use of our resources.<br/>"
        f"Thank you for your cooperation and understanding.<br/><br/>"
        f"Best regards,<br/>"
        f"{hospital_name} Perioperative Leadership Team"
    )


def get_sms_content(content, doctor_name, link, hospital_name):
    return (
        f"{content}"
        f"Dear Dr.{doctor_name}, We hope this message finds you well. We kindly request your assistance in releasing your block time and providing your approval via this link "
        f"{link} on Opmed.ai "
        f"This step is crucial for optimizing our scheduling and ensuring the best use of our resources\n"
        f"Thank you for your cooperation and understanding.\n"
        f"Best regards,\n"
        f"{hospital_name} Perioperative Leadership Team."
    )


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
