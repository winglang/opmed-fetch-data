import json
import requests
import os
import datetime
import time

MAX_DELTA_DAYS = 60

def get_data(url, data, headers):
  for i in range(1, 5):
    r = get_data_base(url, data, headers)
    if r != None:
      return r
    time.sleep(15)
   
  return None

def get_data_base(url, data, headers):
  try:
    r = requests.post(url, json=data, headers=headers, verify=False)
    return r
  except requests.exceptions.RequestException as e:  # This is the correct syntax
    print('request error: {}'.format(e))
    return None

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
  to_date = today + datetime.timedelta(days=21)
  
  if "queryStringParameters" in event and event["queryStringParameters"] != None:
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
  
  r = get_data(url, data, headers)
  if r == None:
    return {
      "statusCode": 200,
      "headers": {
         "Content-Type": "application/json"
      },
      "body": {"error": "fail to fetch data"}
    }        
      
  return {
    "statusCode": 200,
    "headers": {
       "Content-Type": "application/json"
    },
    "body": r.content
  }
