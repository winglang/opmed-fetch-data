import boto3


def send_sms(phone_number: str, message: str, sender_id: str) -> dict:
    sns = boto3.client('sns')
    response = sns.publish(
        PhoneNumber=phone_number,
        Message=message,
        MessageAttributes={
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            },
            'AWS.SNS.SMS.SenderID': {
                'DataType': 'String',
                'StringValue': sender_id
            }
        }
    )
    return response
