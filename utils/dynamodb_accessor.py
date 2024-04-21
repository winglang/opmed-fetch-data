import os

import boto3
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key


class DynamoDBAccessor:
    def __init__(self, table_name, aws_access_key_id=None, aws_secret_access_key=None):
        if aws_access_key_id and aws_secret_access_key:
            self.dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=os.environ['REGION'],
            )
        else:
            self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def get_item(self, tenant_id, data_id):
        try:
            response = self.table.get_item(Key={'tenant_id': tenant_id, 'data_id': data_id})
            return response.get('Item')
        except Exception as e:
            print(f'Error reading from DynamoDB: {e}')
            return None

    def batch_get_item(self, tenant_id, data_ids):
        try:
            request_items = {
                self.table.table_name: {'Keys': [{'tenant_id': tenant_id, 'data_id': data_id} for data_id in data_ids]}
            }
            response = self.dynamodb.batch_get_item(RequestItems=request_items)
            return response['Responses'][self.table.table_name]

        except Exception as e:
            print(f'Error reading from DynamoDB: {e}')
            return None

    def filter_by_field(self, tenant_id, field_name, field_value):
        try:
            key_condition = Key('tenant_id').eq(tenant_id) & Key(field_name).eq(field_value)
            response = self.table.query(
                KeyConditionExpression=key_condition,
                IndexName=field_name,
            )

            return response['Items']

        except Exception as e:
            print(f'Error reading from DynamoDB: {e}')
            return None

    def put_item(self, tenant_id, data_id, data, save_nested=True, metadata=None):
        try:
            item = {
                'tenant_id': tenant_id,
                'data_id': data_id,
            }

            item |= {'data': data} if save_nested else data

            if metadata:
                item |= {'metadata': metadata}

            self.table.put_item(Item=item)

            return True
        except Exception as e:
            print(f'Error writing to DynamoDB: {e}')
            return False

    def batch_put_item(self, tenant_id, data_ids: list, data: list, save_nested=True, metadata=None):
        try:
            with self.table.batch_writer() as batch:
                for data_id, item_data in zip(data_ids, data):
                    item = {
                        'tenant_id': tenant_id,
                        'data_id': data_id,
                    }

                    item |= {'data': item_data} if save_nested else item_data

                    if metadata:
                        item |= {'metadata': metadata}

                    batch.put_item(Item=item)
            return True
        except Exception as e:
            print(f'Error writing to DynamoDB: {e}')
            return False

    def update_item(self, tenant_id, data_id, attribute_updates, metadata=None):
        try:
            if metadata:
                attribute_updates |= {'metadata': metadata}

            updated_expression, expression_attribute_values = get_update_params(attribute_updates)
            res = self.table.update_item(
                Key={'tenant_id': tenant_id, 'data_id': data_id},
                UpdateExpression=updated_expression,
                ExpressionAttributeValues=expression_attribute_values,
            )
            return res['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            print(f'Error updating item in DynamoDB: {e}')
            return False

    def batch_update_item(self, tenant_id, data_ids: list, attribute_updates: list, metadata=None):
        if metadata:
            for attribute_update in attribute_updates:
                attribute_update |= {'metadata': metadata}

        updated_expressions, expression_attribute_values = zip(
            *[get_update_params(attribute_update) for attribute_update in attribute_updates]
        )

        updates = [
            {
                'Update': {
                    'TableName': self.table.table_name,
                    'Key': {'tenant_id': tenant_id, 'data_id': data_id},
                    'UpdateExpression': updated_expression,
                    'ExpressionAttributeValues': expression_attribute_value,
                }
            }
            for data_id, updated_expression, expression_attribute_value in zip(
                data_ids, updated_expressions, expression_attribute_values
            )
        ]
        try:
            response = self.dynamodb.meta.client.transact_write_items(TransactItems=updates)
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            print(f'Error updating item in DynamoDB: {e}')
            return False

    def delete_item(self, tenant_id, data_id):
        try:
            response = self.table.delete_item(Key={'tenant_id': tenant_id, 'data_id': data_id})
            return response
        except Exception as e:
            print(f'Error deleting item from DynamoDB: {e}')
            return None

    def batch_delete_item(self, tenant_id, data_ids: list):
        try:
            delete_items = {
                self.table.table_name: [
                    {'DeleteRequest': {'Key': {'tenant_id': tenant_id, 'data_id': data_id}}} for data_id in data_ids
                ]
            }
            response = self.dynamodb.batch_write_item(RequestItems=delete_items)
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            print(f'Error deleting item from DynamoDB: {e}')
            return None

    def list_items_by_tenant(self, tenant_id):
        try:
            response = self.table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id))
            data_array = [item['data'] for item in response.get('Items', [])]
            return data_array
        except Exception as e:
            print(f'Error querying DynamoDB: {e}')
            return []

    def list_data_ids_by_tenant(self, tenant_id):
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
                ProjectionExpression='data_id',
            )
            return [item['data_id'] for item in response.get('Items', []) if 'data_id' in item]
        except Exception as e:
            print(f'Error querying DynamoDB: {e}')
            return []

    def get_all_items_by_tenant(self, tenant_id):
        try:
            response = self.table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id))
            items_dict = {item['data_id']: item['data'] for item in response.get('Items', [])}
            return items_dict
        except Exception as e:
            print(f'Error querying DynamoDB: {e}')
            return {}


def get_update_params(body):
    """Given a dictionary we generate an update expression and a dict of values
    to update a dynamodb table.

    Params:
        body (dict): Parameters to use for formatting.

    Returns:
        update expression, dict of values.
    """
    update_expression = ['set ']
    update_values = dict()

    for key, val in body.items():
        update_expression.append(f' {key} = :{key},')
        update_values[f':{key}'] = val

    return ''.join(update_expression)[:-1], update_values


def get_blocks_status(start, end, tenant, table_name, fields_to_return: set = None):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    query_params = {
        'KeyConditionExpression': Key('tenant_id').eq(tenant),
        'FilterExpression': Attr('start').between(start, end),
    }
    if fields_to_return is not None:
        query_params['ProjectionExpression'] = ', '.join(fields_to_return | {'data_id'})

    response = table.query(**query_params)

    return {block['data_id']: block for block in response['Items']}
