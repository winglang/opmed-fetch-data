import os

import boto3


class DynamoDBAccessor:

    def __init__(self, table_name, aws_access_key_id=None, aws_secret_access_key=None):
        if aws_access_key_id and aws_secret_access_key:
            self.dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=os.environ['REGION']
            )
        else:
            self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def get_item(self, tenant_id, data_id):
        try:
            response = self.table.get_item(
                Key={
                    'tenant_id': tenant_id,
                    'data_id': data_id
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error reading from DynamoDB: {e}")
            return None

    def put_item(self, tenant_id, data_id, data, save_nested=True):
        try:
            item = {
                'tenant_id': tenant_id,
                'data_id': data_id,
            }
            item |= {'data': data} if save_nested else data
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error writing to DynamoDB: {e}")
            return False

    def update_item(self, tenant_id, data_id, attribute_updates):
        try:
            updated_expression, expression_attribute_values = get_update_params(attribute_updates)
            res = self.table.update_item(
                Key={
                    'tenant_id': tenant_id,
                    'data_id': data_id
                },
                UpdateExpression=updated_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            return res['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            print(f"Error updating item in DynamoDB: {e}")
            return False

    def delete_item(self, tenant_id, data_id):
        try:
            response = self.table.delete_item(
                Key={
                    'tenant_id': tenant_id,
                    'data_id': data_id
                }
            )
            return response
        except Exception as e:
            print(f"Error deleting item from DynamoDB: {e}")
            return None

    def list_items_by_tenant(self, tenant_id):
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id)
            )
            data_array = [item['data'] for item in response.get('Items', [])]
            return data_array
        except Exception as e:
            print(f"Error querying DynamoDB: {e}")
            return []

    def list_data_ids_by_tenant(self, tenant_id):
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
                ProjectionExpression='data_id'
            )
            return [item['data_id'] for item in response.get('Items', []) if 'data_id' in item]
        except Exception as e:
            print(f"Error querying DynamoDB: {e}")
            return []

    def get_all_items_by_tenant(self, tenant_id):
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id)
            )
            items_dict = {item['data_id']: item['data'] for item in response.get('Items', [])}
            return items_dict
        except Exception as e:
            print(f"Error querying DynamoDB: {e}")
            return {}


def get_update_params(body):
    """Given a dictionary we generate an update expression and a dict of values
    to update a dynamodb table.

    Params:
        body (dict): Parameters to use for formatting.

    Returns:
        update expression, dict of values.
    """
    update_expression = ["set "]
    update_values = dict()

    for key, val in body.items():
        update_expression.append(f" {key} = :{key},")
        update_values[f":{key}"] = val

    return "".join(update_expression)[:-1], update_values
