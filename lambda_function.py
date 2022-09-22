import json
import requests
import os
import datetime

def lambda_handler(event, context):
  url = 'https://172.31.3.203:4431/api/external/fullcalendar_events_ajax'
  headers = {
    "Host": "md-booking.hmc.co.il",
    "accept-charset": "utf-8",
    "authorization": os.environ['AUTHORIZATION'],
    "cache-control": "no-cache",
    "content-type": "application/json"
  }
  
  today = datetime.date.today()
  from_date = today - datetime.timedelta(days=3)
  to_date = today + datetime.timedelta(days=27)
  
  data = {
    "event_type": "surgery",
    "start": from_date.strftime("%Y-%m-%d"),
    "end": to_date.strftime("%Y-%m-%d")
  }
  
  r = requests.post(url, json=data, headers=headers, verify=False)
  
  return {
    "statusCode": 200,
    "headers": {
       "Content-Type": "application/json"
    },
    "body": r.content
  }