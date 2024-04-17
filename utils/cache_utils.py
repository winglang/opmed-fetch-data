import json
import os

import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client(
    's3',
    config=boto3.session.Config(
        signature_version='s3v4',
    ),
)
bucket_name = os.environ.get('CACHE_BUCKET')


def get_cache(key):
    try:
        response = json.loads(s3_client.get_object(Bucket=bucket_name, Key=key)['Body'].read())
        print(f'retrieved cache for {key}')
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f'No such key: {key}')
        else:
            print(e)


# Upload the file to S3
def update_cache(response_body, key):
    try:
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=response_body)
    except Exception as e:
        print(e)
