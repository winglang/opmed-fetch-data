import boto3


class DynamoDBAccessor:
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def get_item(self, tenant_id, data_id):
        try:
            response = self.table.get_item(
                Key={
                    'tenantId': tenant_id,
                    'dataId': data_id
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error reading from DynamoDB: {e}")
            return None

    def put_item(self, tenant_id, data_id, data):
        try:
            item = {
                'tenantId': tenant_id,
                'dataId': data_id,
                'data': data  # Assuming the entire JSON object is stored under the 'data' attribute
            }
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error writing to DynamoDB: {e}")
            return False

    def delete_item(self, tenant_id, data_id):
        try:
            response = self.table.delete_item(
                Key={
                    'tenantId': tenant_id,
                    'dataId': data_id
                }
            )
            return response
        except Exception as e:
            print(f"Error deleting item from DynamoDB: {e}")
            return None

    def list_items_by_tenant(self, tenant_id):
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenantId').eq(tenant_id)
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error querying DynamoDB: {e}")
            return []

    def list_data_ids_by_tenant(self, tenant_id):
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenantId').eq(tenant_id),
                ProjectionExpression='dataId'
            )
            return [item['dataId'] for item in response.get('Items', []) if 'dataId' in item]
        except ClientError as e:
            print(f"Error querying DynamoDB: {e}")
            return []
