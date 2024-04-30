from utils.send_notification.send_email import send_email
from utils.send_notification.send_sms import send_sms


def send_proactive_block_release_notification(
    nudge_method, hospital_name, recipients, nudge_content, doctor_name, link_for_surgeon
):
    match nudge_method:
        case 'send-email':
            subject = 'Request for unused block time release'
            email = {'html': get_email_content(nudge_content, doctor_name, link_for_surgeon, hospital_name)}
            send_email(subject=subject, body=email, recipients=recipients)
            res = 'Sent nudge email'
        case 'send-sms':
            sms_txt = get_sms_content(doctor_name, link_for_surgeon, hospital_name)
            send_sms(recipients[0], sms_txt, sender_id=hospital_name)
            res = 'Sent nudge sms'

        case _:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': f'Method not found: {nudge_method}',
            }
