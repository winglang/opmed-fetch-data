import json

import boto3


def store_s3_with_acl(bucket_name, s3_key, response_body):
    try:
        s3 = boto3.client('s3')
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=json.dumps(response_body))
        s3.put_object_acl(Bucket=bucket_name, Key=s3_key, ACL='authenticated-read')
        print('Success: Saved to S3')
    except Exception as e:
        print('Error: {}'.format(e))
