import json
import requests

def lambda_handler(event, context):
  url = 'https://172.31.3.203:4431/api/external/fullcalendar_events_ajax'
  headers = {
    "Host": "md-booking.hmc.co.il",
    "accept-charset": "utf-8",
    "authorization": os.environ['AUTHORIZATION'],
    "cache-control": "no-cache",
    "content-type": "application/json",
    "postman-token": "2df6e60a-b265-e628-e1be-7ae751feb52c"
  }
  data = {
    "event_type": "surgery",
    "start": "2022-09-18",
    "end": "2022-09-30"
  }
  r = requests.post(url, json=data, headers=headers, verify=False)
  print(r.content)
  r.json()
    
  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Lambda!')
  }