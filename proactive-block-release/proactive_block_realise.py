import decimal
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import boto3
import requests
from boto3.dynamodb.conditions import Key, Attr

from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS, get_service

url = os.getenv('URL')
blocks_status_table_name = os.getenv('BLOCKS_STATUS_TABLE_NAME')

BLOCK_FIELDS_TO_RETURN = ['lastUpdated', 'releaseStatus', 'acceptedMinutesToRelease']


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super().default(o)


def get_blocks_status(start, end, tenant):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(blocks_status_table_name)

    response = table.query(
        KeyConditionExpression=Key('tenant_id').eq(tenant),
        FilterExpression=Attr('start').between(start, end)
    )

    return {block['data_id']: {k: v for k, v in block.items() if k in BLOCK_FIELDS_TO_RETURN} for block in
            response['Items']}


def get_blocks_predictions(fetch_data, headers):
    data_to_predict = {
        'blocks': fetch_data["blocks"],
        'tasks': fetch_data["tasks"],
        "metadata": {
            "use_ai_predictions": True,
            "min_task_pred_abs": 15,
            "min_task_pred_percent": 0,
            "min_block_pred_abs": 0,
            "min_block_pred_percent": 0,
            "ignored_tasks_list": [],
            "ignored_blocks_list": []
        }
    }

    return requests.post(f'{url}/block-population-risk', json=data_to_predict, headers=headers)


def proactive_block_realise(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers'])

    print(f'username: {username}')

    tenant = get_service(event)
    print(f'tenant: {tenant}')

    default_from_value = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')  # Today + 3 days
    default_to_value = (datetime.now() + timedelta(days=31)).strftime('%Y-%m-%d')  # Today + 31 days
    queryStringParameters = {key: val for key, val in event.get('queryStringParameters', {}).items() if
                             key in ['from', 'to']}
    queryStringParameters['from'] = queryStringParameters.get('from', default_from_value)
    queryStringParameters['to'] = queryStringParameters.get('to', default_to_value)

    headers = {key: val for key, val in event.get('headers', {}).items() if
               key.lower() in AUTH_HEADERS}

    fetch_data = requests.get(f'{url}/fetch-data/v2', params=queryStringParameters, headers=headers).json()

    for task in fetch_data['tasks']:
        if 'start' in task:
            task['start_time'] = task.pop('start')
        if 'end' in task:
            task['end_time'] = task.pop('end')
        if 'resources_ids' in task:
            task['resources'] = task.pop('resources_ids')

    with ThreadPoolExecutor() as executor:
        get_blocks_predictions_future = executor.submit(get_blocks_predictions, fetch_data, headers)
        get_blocks_status_future = executor.submit(get_blocks_status, queryStringParameters['from'],
                                                   queryStringParameters['to'], tenant)

        blocks_predictions_res = get_blocks_predictions_future.result()
        blocks_status = get_blocks_status_future.result()

    if blocks_predictions_res.status_code == 200:
        predicted_blocks = blocks_predictions_res.json()['blocks']
        for block in predicted_blocks:
            block |= blocks_status.get(block['id'], {'releaseStatus': 'new'})
        response_body = json.dumps(predicted_blocks, cls=DecimalEncoder)
    else:
        response_body = blocks_predictions_res.text
    save_to_s3 = (event.get("queryStringParameters") or {}).get("save_to_s3", False)
    if save_to_s3:
        s3_key = os.path.join(tenant, "proactive-block.json")
        bucket_name = os.environ['BUCKET_NAME']
        try:
            s3 = boto3.client('s3')

            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=json.dumps(response_body)
            )

            s3.put_object_acl(
                Bucket=bucket_name,
                Key=s3_key,
                ACL='authenticated-read'
            )

            print("Success: Saved to S3")
        except Exception as e:
            print("Error: {}".format(e))

    return {
        "statusCode": blocks_predictions_res.status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": response_body
    }


if __name__ == '__main__':
    event = {
        "queryStringParameters": {
            'from': '2024-03-01',
            'to': '2024-05-01',
            'save_to_s3': True
        },
        'headers': {
            "gmix_serviceid": "hmc-users",
            "referer": f'{url}/',
            "Cookie": '_ga=GA1.1.969208942.1695724749; _ga_KY8PNQLTFN=GS1.1.1713162598.84.1.1713162750.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.KxTRsgdNx2WjRYOWTQ_O9LsQu3of2e9X7zmtGleK9ge-XsJqe7_RCoOAHe3C4pGVoHARqwruaUppO_z9e54RwuFCDFNTqMVgaJyJglkOkYGyBc6v0c0KAFtkZulUe-VZKbpvvBRvP1M1FeS4iklojRjySaatKAC-kAmUEO5n5EohDBp2t8ESP5TKJCTzJW98jGGteUiZFKAnGNggad5A962e2Rn0hkq8iFlfVQd9EuCUdCBVcGG0Y6Ri0oheF38owozJpW0ozmPF3CIk7cl-OVli3s1hiSQY9aMFxt7UIwPcg17RVnl86fPImcbV0a3XzqCyvG6pbYehj5IepCmzQQ.pCyrXKK7BAB1uXP5.KYsiSy_OKYjoJQtpDwnGypN7ZyTH6LA5fDoIL4-mIAOAuHZk5M78PAt1pJsmmF0QmhPsDVu5fweR1DvCmUQrdJstteuGGY3W24FiIovzZIFqwtG_3gtRIhEWL3NdyRd0N7x7IaPLEwuM2Vayswz5frqzCadCHibdrLDeaDn2hsbJGVWnd9sltkTQCjuVkkwnZzF2ERM3H8-e4MpTN03n5-yA3UOoZezTHGbDT_P0QBOriNku90nq3ygV1sOJlxA-3P5EkD3ak832DXaWFw8R_GfYvJXaoArWZ1sm-g3KpkDHDeRdiOLP6cskf7pdviFS0Cyj90DipiLQJkoR-Z4ks3_BlnjbMBvYD2OVYqV6hJGgwirSnWT_sjfEzN9DObMH84q9AP_QblQQ_26FLGZakUQvIuWgBemOb84CVIPU8X88TfYwNUX0ETGm_DhukM9ci3aeIq1Dv94EVKfeWGMIvmXY_zzFHhr6wCkry4Wy7MUNAFsGuWIcZ7YT-h-yha_vMTMYRU45Yuiaz85PBpRoV_J8XSE7n_13PodekcLgOdIOZJejdxsIihZSYcBu6-kGH29WwN_7s2CsyvhOCIS4IN1XeVcrktv5zC0EeHtANqNex1YOTNAA77lDidZo3u3L03tRMmn5HYvSm_4pR8-RSIqarj5oyFoueyainswSoKuc576NYWuCIMUAIUNwGfKEPuZTb1nQ-gXXPRVpVjE81oj8OZngwuD5rPsPRTOxAtrGzKfzQf_Gx8z9lATvQhMpwAdL066iRheVkrB7tKIJxMJVnoRV0c4nPr18gbbn0ZfuUxiceGVUWH68RHt3JLJMgZvQVidD7lWtnEikuJ3vQQYfgESHRzrLjf2Raa94hCCo5f_Y3mteWyGri7JbS0-jvpSUS-ywe8h5WCJabChFkpCo_HAKMi7f1tLlY5Vfunwy0Elap6yQWZva0z9lQ_y0boARDWcvfzRuI8QiYqOEfFObujPp0vvnco1_x0y-s365UOeSddcR5ja4Swq-LRvWhTujWoTz2vPnzVrDovrdDUae7W66ZJ-JYXnEjgYo0xrw8FJlzlgeNSAyvICbMEfn7GW01BEYGNy5IozVMfaY-1VPwCpqZog0iOTffH0f8tZQycjGW5494kIQxt35JUFFkVrX0aVJ4T1u2K5dRtHVTi9sz7uK6eDzKlWdeiaI2hmkPg51XTRSL1tGpc5qFjC3RTJ9CLDNRY2vEVzPl7vp91NRswIX8nGypqJSJvtCjxOO-qUVJ5Vsfc1b7JAzpNUfDVgKE8iKH5InERsGG2cAfkIBEJYwSe4Hl4cHnbvAPPaCDCUCkmZ9E27p6uOUEllQIzG4EnrAGgfsgPA0Yw0UfQ.KQWFwwK76pYFGBW_okY4Dw; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=omri@opmed.ai; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzY2FlNDI0NS0wOTI2LTQ1MzMtYWIwMi04NzZlMGI4MGQ0MjMiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJtYXlvLXVzZXJzIiwiZmhpci11c2VycyIsIm5iaS11c2VycyJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwib3JpZ2luX2p0aSI6ImVhODllODk3LWRmNDAtNGQyYy04NjA2LTk2NDZlYWIyZjljNiIsImV2ZW50X2lkIjoiMjJkNjcwNzEtMzE2MS00Nzc2LWJjYTMtYTE4ZjUwNTliYjVkIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiBwaG9uZSBvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF1dGhfdGltZSI6MTcxMzE2Mjc1NCwiZXhwIjoxNzEzMTc5NTU4LCJpYXQiOjE3MTMxNjUxNTgsImp0aSI6IjFjZjk0MzljLWQxNzUtNGI4YS04MjIzLWJkMjZkODVkOTA1ZiIsInVzZXJuYW1lIjoib21yaUBvcG1lZC5haSJ9.Hlb2UQICh75GNEQoPZahvOjhgvoHuAxV0B8FUvOgOLHef5k3l0srltJGcHPox02Ea_vj26ZPFffdGDpChsSPzvrH9VQoQ4DYc16LyDXzzef05S1e3iAN0Bf60wOVKlYpDtORei9MgflduA98osAY43N30SFArPCq3pwvdF99FX83qARJYBu4r12aQmGo9d9j_R1WbHhdUo0KLhoLB0tD6_VCInDuXbHic8j1ZAHItUo0S1r4HA9pJcIuNCC_iZw84QSXMmvjI65YbEsnB1pgALoJAd3lenAvItFg8x4E8Dg4rxYZK1MYG9hB5zp0BldxGVeaqdHg4bhX1yOtui6zKg; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiWjhfY2F6TnRoekZBclpMNnRLMG1hUSIsInN1YiI6IjNjYWU0MjQ1LTA5MjYtNDUzMy1hYjAyLTg3NmUwYjgwZDQyMyIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsIm1heW8tdXNlcnMiLCJmaGlyLXVzZXJzIiwibmJpLXVzZXJzIl0sImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJjb2duaXRvOnVzZXJuYW1lIjoib21yaUBvcG1lZC5haSIsIm9yaWdpbl9qdGkiOiJlYTg5ZTg5Ny1kZjQwLTRkMmMtODYwNi05NjQ2ZWFiMmY5YzYiLCJjb2duaXRvOnJvbGVzIjpbImFybjphd3M6aWFtOjoyNzM2MDUwOTcyMTg6cm9sZVwvY29nbml0b19hY2Nlc3MiXSwiYXVkIjoiMzRyZzhlc3Q1aTM0cW40a29rdDFjMGt2aSIsImV2ZW50X2lkIjoiMjJkNjcwNzEtMzE2MS00Nzc2LWJjYTMtYTE4ZjUwNTliYjVkIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3MTMxNjI3NTQsImV4cCI6MTcxMzE3OTU1OCwiaWF0IjoxNzEzMTY1MTU4LCJqdGkiOiI4NTk2ZjEyNi05MjkyLTQ3YTQtOTAyZC1hZWZhZGRhMWIyNmEiLCJlbWFpbCI6Im9tcmlAb3BtZWQuYWkifQ.DDzKBLlnXC00vqFrSrDqBDekfkJ8hBbP7bBrMdgGHRpGVJVIDtteDa0i_JPeBUYp5DGD3ff42pau6CHRlmL6HQiq98OXN3b0PUjwf05smy4vuSKonr5TRlCxoZmHS9nK_-_aeme7Wad-1US085KY_GK8YsNSS_zYqvzbNvf11yZRSIxN1O8P5UmiNTVGD6YsDbkCVXWhOuXwLHnTdCxQVRTmGOCvGsanZHuVMBhc2YYuVaP6zHHmnCmvQyjbZh7mNlphKOKTAdbCsraZjV544Cbtrv6rL9UZi5rIXkXyOeaqRHuC7uOySRd0Yvm4vZ36uPFEUMPZ1d3-JZ0d6o3qqg; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18ad1123ed147-0d7e87ea127c31-18525634-1fa400-18ad1123ed147%22%2C%22%24device_id%22%3A%20%2218ad1123ed147-0d7e87ea127c31-18525634-1fa400-18ad1123ed147%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1713165278.385.1.1713165279.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)

    print(time.time() - t)
    pass
