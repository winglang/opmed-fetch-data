import json
import requests
import os
import datetime

MAX_DELTA_DAYS = 60

def lambda_handler(event, context):
  url = '{}/api/external/fullcalendar_events_ajax'.format(os.environ['HAPROXY_PATH'])
  headers = {
    "Host": os.environ['HOST'],
    "accept-charset": "utf-8",
    "authorization": os.environ['AUTHORIZATION'],
    "cache-control": "no-cache",
    "content-type": "application/json"
  }
  
  today = datetime.date.today()
  from_date = today - datetime.timedelta(days=3)
  to_date = today + datetime.timedelta(days=27)
  
  if "queryStringParameters" in event:
    if "from" in event["queryStringParameters"]:
      from_date = datetime.datetime.strptime(event["queryStringParameters"]["from"], "%Y-%m-%d")
    if "to" in event["queryStringParameters"]:
      to_date = datetime.datetime.strptime(event["queryStringParameters"]["to"], "%Y-%m-%d")
      
  delta_days = to_date - from_date
  if delta_days.days > MAX_DELTA_DAYS:
    return {
      "statusCode": 200,
      "headers": {
         "Content-Type": "application/json"
      },
      "body": {"error": "delta is more than 60 days"}
    }    
  
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