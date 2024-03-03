import json
from datetime import datetime

from proactive_nudge_reminder.send_email import send_email
from utils.services_utils import lowercase_headers, get_username


def send_reminder(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    block = json.loads(event['body'])
    block['start_time'] = datetime.fromisoformat(block['start_time'])

    print(f'username: {username}')

    method = event['path'].rsplit('/', 1)[-1]
    if method == 'send-email':
        subject = f'Request for Adjusted Surgery Duration on {datetime.strftime(block['start_time'], "%b %d, %Y")}'
        email_text = create_fancy_notification(block)
        send_email(subject=subject, body={'text': email_text})
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


def create_fancy_notification(block):
    return (f"Dear {block['surgeon_name']},\n"
            f"I hope this message finds you well. "
            f"I am writing to discuss the upcoming surgery scheduled for {datetime.strftime(block['start_time'], "%b %d, %Y")}, at {datetime.strftime(block['start_time'], "%H:%M %p")}  in {block['room_id']}, which is currently allocated a block time of {block['original_duration']} hours."
            "\n\n"
            f"Upon thorough review of the pre-operative planning and predictive analyses, it has come to our attention that the anticipated duration of this procedure may be overestimated."
            f" Based on the detailed simulations and historical data for similar cases, we have a strong conviction that the surgery could be efficiently completed within an {block['predicted_duration']}-hour timeframe without compromising the quality of care or patient safety."
            f"\n\n"
            f"Would it be possible to review the current plan and consider this adjustment?")
