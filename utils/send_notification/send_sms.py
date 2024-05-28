import boto3
from wing import try_lifted

def send_sms(phone_number: str, message: str, sender_id: str) -> dict:
    sns = try_lifted('sns') or boto3.client('sns')
    response = sns.publish(
        PhoneNumber=phone_number,
        Message=message,
        MessageAttributes={
            'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': 'Transactional'},
            'AWS.SNS.SMS.SenderID': {'DataType': 'String', 'StringValue': sender_id},
        },
    )
    return response
