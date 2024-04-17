import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3


def send_email(subject, body, attachments=None, recipients=None):
    attachments = attachments or []

    recipients = recipients or os.environ.get('recipients').split(', ')
    sender = os.environ.get('sender') if 'sender' in os.environ else 'bot@opmed.ai'

    msg = create_multipart_message(sender, recipients, subject, body.get('text'), body.get('html'), attachments)
    ses_client = boto3.client('ses')  # Use your settings here
    return ses_client.send_raw_email(Source=sender, Destinations=recipients, RawMessage={'Data': msg.as_string()})


def create_multipart_message(
    sender: str, recipients: list, title: str, text: str = None, html: str = None, attachments: list = None
) -> MIMEMultipart:
    """
    Creates a MIME multipart message object.
    Uses only the Python `email` standard library.
    Emails, both sender and recipients, can be just the email string or have the format 'The Name <the_email@host.com>'.

    :param sender: The sender.
    :param recipients: List of recipients. Needs to be a list, even if only one recipient.
    :param title: The title of the email.
    :param text: The text version of the email body (optional).
    :param html: The html version of the email body (optional).
    :param attachments: List of files to attach in the email.
    :return: A `MIMEMultipart` to be used to send the email.
    """
    multipart_content_subtype = 'alternative' if text and html else 'mixed'
    msg = MIMEMultipart(multipart_content_subtype)
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    # Record the MIME types of both parts - text/plain and text/html.
    # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
    if text:
        part = MIMEText(text, 'plain')
        msg.attach(part)
    if html:
        part = MIMEText(html, 'html')
        msg.attach(part)

    # Add attachments
    for attachment in attachments or []:
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read())
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
            msg.attach(part)

    return msg
