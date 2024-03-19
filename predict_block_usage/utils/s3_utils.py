import io
import json
import os
from datetime import datetime, time

import boto3
import pandas as pd


def get_s3_client():
    # Create a Boto3 S3 client
    if os.getenv('env', None) == 'local':
        s3client = boto3.client('s3',
                                 aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                 config=boto3.session.Config(signature_version='s3v4'))
    else:
        s3client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))
    return s3client


s3_client = get_s3_client()


def get_s3_object(filename, bucket):
    # if filename is json, return json
    if filename.endswith('.json'):
        return get_s3_json(filename, bucket)
    if filename.endswith('.csv'):
        return get_s3_csv(filename, bucket)


def get_s3_json(filename, bucket):
    data = s3_client.get_object(Bucket=bucket, Key=filename)["Body"].read()
    json_file = json.loads(data)
    return json_file


def get_s3_csv(filename, bucket):
    cached_data = s3_client.get_object(Bucket=bucket, Key=filename)["Body"].read()
    return pd.read_csv(io.BytesIO(cached_data), encoding='utf8')


def get_delta_files_from_s3(bucket, last_date, morning_start_time, morning_end_time):
    files_name_list = get_items_from_s3(bucket)
    relevant_files_dict = {}
    for file_name in files_name_list:
        # Extract the datetime from the file name (assuming format 'fetch.YYYYMMDDHHMMSS.json')
        file_datetime_str = file_name.split('.')[1]
        file_datetime = datetime.strptime(file_datetime_str, '%Y%m%d%H%M%S')

        # Extract the date and check if the time is after 6AM
        file_date = file_datetime.date()

        if file_datetime > last_date:  # take only the new files
            if (file_datetime.time() >= time(morning_start_time, 0)) and \
                    (file_datetime.time() <= time(morning_end_time, 0)):
                if file_date not in relevant_files_dict:
                    relevant_files_dict[file_date] = file_name
    return list(relevant_files_dict.values())


def get_items_from_s3(bucket):
    # get all filenames in s3 bucket
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket)

    items = []
    for page in page_iterator:
        if page['KeyCount'] > 0:
            items += [item for item in page['Contents']]

    return [item['Key'] for item in items]  # [:2]

def put_item_in_s3(bucket, key, body, acl_needed=False):
    # Upload the CSV string to the specified file in the S3 bucket
    response = s3_client.put_object(Bucket=bucket, Key=key, Body=body)
    # Set the object ACL to grant read permissions to authenticated users

    if acl_needed:
        s3_client.put_object_acl(
            Bucket=bucket,
            Key=key,
            ACL='authenticated-read'
        )

    # Check if the upload was successful
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print(f"File uploaded successfully! path: {bucket}/{key}")
    else:
        print("Failed to upload scheduled file. error code: ", response['ResponseMetadata']['HTTPStatusCode'])
