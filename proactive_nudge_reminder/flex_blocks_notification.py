from proactive_nudge_reminder.notification_message_details import NotificationMessage
from utils.send_notification.send_email import send_email
from utils.send_notification.send_sms import send_sms


def send_flex_blocks_notification(nudge_method: str, notification_message: NotificationMessage):
    match nudge_method:
        case 'send-email':
            subject = 'Opportunity to increase block time'
            email = {'html': get_email_content(notification_message)}
            send_email(subject=subject, body=email, recipients=notification_message.recipients)
            return 'Sent nudge email'
        case 'send-sms':
            sms_txt = get_sms_content(notification_message)
            send_sms(notification_message.recipients[0], sms_txt, sender_id=notification_message.hospital_name)
            return 'Sent nudge sms'

        case _:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': f'Method not found: {nudge_method}',
            }


def get_email_content(notification_message: NotificationMessage) -> str:
    return (
        f"<img src='https://gmix-sync.s3.amazonaws.com/public-items/opmed-logo.png' alt='' />{notification_message.nudge_content}"
        f'<br/>Dear Dr.{notification_message.doctor_name}<br/>We hope this message finds you well.<br/>'
        f'<br/>Your attached blocks popped up as potential for booking additional surgeries and we are willing to extend their length.'
        f' We would like your reply via the '
        f'attached <a href={notification_message.link_for_surgeon}>link</a> on Opmed.ai <br/>'
        f'This step is crucial for optimizing our scheduling and ensuring the best use of our resources.<br/>'
        f'Thank you for your cooperation and understanding.<br/><br/>'
        f'Best regards,<br/>'
        f'{notification_message.hospital_name} Perioperative Leadership Team'
    )


def get_sms_content(notification_message: NotificationMessage) -> str:
    return (
        f'Dear Dr.{notification_message.doctor_name}, We hope this message finds you well. '
        f'We kindly request your assistance in improving room utlization by extending your blocks time. '
        f'Please provide your approval via this link '
        f'{notification_message.link_for_surgeon} on Opmed.ai\n'
        f'This step is crucial for optimizing our scheduling and ensuring the best use of our resources\n'
        f'Thank you for your cooperation and understanding.\n'
        f'Best regards,\n'
        f'{notification_message.hospital_name} Perioperative Leadership Team.'
    )
