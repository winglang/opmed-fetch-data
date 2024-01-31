import argparse
import sys

import boto3
import json
import os

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from utils.dynamodb_accessor import DynamoDBAccessor


def read_json_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    file_content = response['Body'].read()
    json_data = json.loads(file_content)
    return json_data


def write_to_dynamodb(dynamodb_accessor, tenant_id, data):
    for key, value in data.items():
        data_id = key
        dynamodb_accessor.put_item(tenant_id, data_id, value)


def main(is_prod, tenant_id):
    # Check if AWS environment variables are set
    if 'AWS_ACCESS_KEY_ID' not in os.environ or 'AWS_SECRET_ACCESS_KEY' not in os.environ:
        raise EnvironmentError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables must be set.")

    bucket_name = 'gmix-sync'
    file_key = f'{tenant_id}/service.json'
    dynamodb_table_name = 'tenants-params-dev' if is_prod is False else 'tenants-params'

    dynamodb_accessor = DynamoDBAccessor(dynamodb_table_name, os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
    json_data = read_json_from_s3(bucket_name, file_key)
    write_to_dynamodb(dynamodb_accessor, tenant_id, json_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import json into dynamoDB.tenants-params[-dev]")
    parser.add_argument("tenant_id", type=str, help="Tenant ID")
    parser.add_argument("env", type=str, choices=['prod', 'dev'], help="Import to Prod table")

    args = parser.parse_args()
    prod = args.env == 'prod'
    main(prod, args.tenant_id)

# HOWTO:
# export AWS_ACCESS_KEY_ID=
# export AWS_SECRET_ACCESS_KEY=
# export REGION=us-east-1
# python import_tenants_params.py fhir-users dev
# NOTE: THis script will override existing records!

