import json
import requests

def lambda_handler(event, context):
    # TODO implement
    r = requests.post('https://github.com/timeline.json')
    r.json()
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
