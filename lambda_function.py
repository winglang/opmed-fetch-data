import json
import requests
import os
import datetime
import time
import boto3

MAX_DELTA_DAYS = 370

def get_data(url, data, headers):
  for i in range(0, 1):
    r = get_data_base(url, data, headers)
    if r != None:
      return r
    time.sleep(20)
   
  return None

def get_data_base(url, data, headers):
  try:
    r = requests.post(url, json=data, headers=headers, verify=False)
    if int(r.status_code) != 200:
      print('ERROR: request error: {} {}'.format(r.text, r.status_code))
      print('ERROR: request request: {}'.format(r))
      print('ERROR: request headers: {}'.format(r.headers))
      return None  
    
    print('request success'.format(r))
    return r
  except Exception as e:
    print('ERROR: request error: {}'.format(e))
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
  from_date = default_from_date = today - datetime.timedelta(days=3)
  to_date = default_to_date = today + datetime.timedelta(days=21)
  save_to_blob = False

  print("event: {}".format(event))  
  if event is not None and "body" in event and event["body"] is not None and "save" in event["body"]: 
    save_to_blob = True
  if event is not None and "save" in event:
    save_to_blob = True

  if "queryStringParameters" in event and event["queryStringParameters"] != None:
    if "from" in event["queryStringParameters"]:
      from_date = datetime.datetime.strptime(event["queryStringParameters"]["from"], "%Y-%m-%d")
    if "to" in event["queryStringParameters"]:
      to_date = datetime.datetime.strptime(event["queryStringParameters"]["to"], "%Y-%m-%d")
      
    if "save" in event["queryStringParameters"]:
      save_to_blob = True
      
  delta_days = to_date - from_date
  if delta_days.days > MAX_DELTA_DAYS:
    from_date = default_from_date
    to_date = default_to_date
  
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

  if save_to_blob:
    try:
      s3 = boto3.resource('s3')
      s3object = s3.Object(os.environ['BUCKET_NAME'], 'fetch.{}.json'.format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
      s3object.put(
        Body=r.content
      )
      print("Success: Saved to S3")
    except Exception as e:
      print("Error: {}".format(e))
      
  return {
    "statusCode": 200,
    "headers": {
       "Content-Type": "application/json"
    },
    "body": r.content

  }
