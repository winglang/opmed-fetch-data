import json

import boto3


def invoke_lambda_function(function_name, event):
    lambda_client = boto3.client('lambda')

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',  # or 'Event' for asynchronous
        Payload=json.dumps(event)
    )

    # Read the response (if needed)
    response_payload = json.loads(response['Payload'].read())

    if error := response.get('FunctionError'):
        raise Exception(f'Error invoking {function_name}: {error}, {response_payload}')

    return json.loads(response_payload['body'])
