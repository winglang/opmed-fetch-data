import decimal
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import boto3
import requests
from boto3.dynamodb.conditions import Key, Attr

from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS, get_service

url = os.getenv('URL')
blocks_status_table_name = os.getenv('BLOCKS_STATUS_TABLE_NAME')

BLOCK_FIELDS_TO_RETURN = ['lastUpdated', 'releaseStatus', 'acceptedHours']


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

    queryStringParameters = {key: val for key, val in event.get('queryStringParameters', {}).items() if
                             key in ['from', 'to']}
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
    save_to_s3 = event["body"].get("save_to_s3", False)
    if save_to_s3:
        s3_key = " proactive-block.json"
        bucket_name = os.environ['BUCKET_NAME']
        try:
            s3 = boto3.resource('s3')
            s3object = s3.Object(bucket_name, s3_key)
            s3object.put(
                Body=response_body
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
            'to': '2024-05-01'
        },
        'headers': {
            "gmix_serviceid": "hmc-users",
            "referer": 'https://plannerd.greatmix.ai/',
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.521.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; _ga_KY8PNQLTFN=GS1.1.1710233738.35.0.1710233738.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJmaGlyLXVzZXJzIl0sImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsInZlcnNpb24iOjIsImNsaWVudF9pZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJvcmlnaW5fanRpIjoiNzQyOWFmMGEtZWU0NS00NzJhLTg0ODMtM2RlYTI5YmJmNDY2IiwiZXZlbnRfaWQiOiJhYjcwMWU1MS04MWY5LTQzM2ItYWM2ZC1iMzAxZDZmMGEyNjkiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6ImF3cy5jb2duaXRvLnNpZ25pbi51c2VyLmFkbWluIHBob25lIG9wZW5pZCBwcm9maWxlIGVtYWlsIiwiYXV0aF90aW1lIjoxNzEwNjg3MjYyLCJleHAiOjE3MTA3MDE2NjIsImlhdCI6MTcxMDY4NzI2MiwianRpIjoiMTJjMzJkZTYtNmZiNi00NmY5LWFjZjAtNzE4Y2UyZTIwMjdhIiwidXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.eN1jey2u0c_rO-gwvEnRyM-PKgi2karr7oBTd7v_0VKEPkYg-6o_VkTB_buZWRfpxlbh5uL61S0x5YU43tZ61F953PkvMSMOsc3c4BYYHlXIqfXKdrazYpYmR0UGo4v-yWCgZGaoR5uSGdmb9iu6idhJfOGB4ajXX2dZcrfxw0-ljcq_GrF6sBMllYgrnV2qeLkpM-60FoLRwT5Xxt7vO-PHVRryWIDN0jqIyiXcI_fg4Ticni2j6L5_Af81u_gnoLu6Iq8VSWh_6XKBYlUISIsSD_i4T5H30AiDOIK-pRWJAqJWXFSvThbRdVa1KnwEp1G5GttgFVlXCkdAtNuM2g; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoic2xTdTk4N2hMYlEzNkRVaXoxUVhQdyIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsImZoaXItdXNlcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsImNvZ25pdG86dXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkiLCJvcmlnaW5fanRpIjoiNzQyOWFmMGEtZWU0NS00NzJhLTg0ODMtM2RlYTI5YmJmNDY2IiwiY29nbml0bzpyb2xlcyI6WyJhcm46YXdzOmlhbTo6MjczNjA1MDk3MjE4OnJvbGVcL2NvZ25pdG9fYWNjZXNzIl0sImF1ZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJldmVudF9pZCI6ImFiNzAxZTUxLTgxZjktNDMzYi1hYzZkLWIzMDFkNmYwYTI2OSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzEwNjg3MjYyLCJleHAiOjE3MTA3MDE2NjIsImlhdCI6MTcxMDY4NzI2MiwianRpIjoiMmFmZTZjMjYtM2QyOC00YmRiLWFhNmMtMWMyM2NlYzIxMTU4IiwiZW1haWwiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.NbTIMuT_OH8tQbkoRRPSVaec7L7BnB7C9dWsB1Iy-R4cYoozrUatLnoriHa_pQYKgWGpihfOgoRcyLYyUALGCcKrHmn-MRcqPb7k2T1oXCptFS6Vx1rm-6N6eByZdSwRwtaAaYZt_48aVaH8oof1OkiVLQgBvMKK6RWS-qnGmjQ6sItE220-1EIwSIDmpVfKuD_K4TMt8P38S_I5XV5Xws2oh9DAic3ul1F4zBh6EqQqLZPtuhgZZP1nkXyNjIT9emmWmYxJPttP4-cCyOrsoSwk7bdA46KO4LkD7v5v4U9n3l-Wn0jRaQTlz3cKxN0FodS6z4NHjI5Ygef-jtMDTw; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.kxI5jNPsgbmiMg4Ll94E9HlQ2syxudw3jxWOQt2xZHN83u4-9L4RQWlWYloVLVuQNFImBxpWpOyEw_aaJZJi4bzgn3S5rgeipCblI4KFFbZMekLwQKw9GQjPToxyQu-yV-EUxaZ1CE7Y-CsDeW_gg7eSp8BmiJiO0CKAfsoUU_-zq8m-qhHGXRFF9t5JZxsF6GkdFxSTLZOf3sclabb3KjNpv1dI2NyX2lNGDyT9BMjmfzk2YZ3RNAjU0UVBH7K1NiRrwrShQ-EbAqMZMooy3LiYrVCBaAcq8-3qliAMOsAA1z0pJrH8_XAXxfktQojDS2JGKFqgKTnBMexP7GGgYQ.iE-I-o6JvUgEyw6B.TxeqoRxnfRarRRa4T4KQ_g6aXE3_PJSCMuJkqINypcJSMKtMTx7EakF2jDL9_TBdG3dTIKv6_lICJ5UAq3KrbVgg1PSv2on4daugMTm-IzuZLCeHEOp-R8yuI27hRoZtYfqTh6i4mOVU3-1PsoNgVVKckkEkt5V8T8BJB0qO5Itgoz9sW9A5iuVYZSsBekBxLnEvD_OXQVQmZR11-qjeXqRuXaKDfTZT6FynebP78ZCVfyrIU5_zIXewiDUasZjnUGgEpRMR5miaZuX_R74eAFjontttNxu2BZeeT79UIzodrxqosTJWx2OtpyujXrIUc19c0eMkhEnlGKfkCNYcgk6ADWvkCgCooerlhM_DxorHIH13Ebj4sTrHtlLCfEURRxakYP13ERd8_80Q_qMV5bnYsAJ_duH-d5ZA6srgY7xbzyrT8rRn7eBcDjxAVpZaCeZSzs18BxIMtK7Mslitube-mN0tPeimttSFV18_8mgYNrl_3sjtkRs94CN1gjXFi6MlH4C4cQfVdovz5szI_XHox53hmdaEznhGr2B-dSDZVDXb0MjijfgfNMvgbaSyu3NVSSQoI32cNh8F_huixOB2j5dPlGXjlJKo7FA2waKHm-tQb-1DYnaaHVvxCs30lybn3QmlL1vyQoKTXNom5lpR5BFYxswQ27A9N846incHHz_DeI-YRhtDn-Z-gK9LUOY7nWxwTGd9rNGVHtrPxnNwzP3YMj6O7T70qBZ-KuN8XRSCI61yhNQ9ocg_Tz5PqU5KM5VuK7ttSVfKlrltUPai9XZQs5FwT-o0vMC2znEq0otvjDfxDSbeB5mBMwKNFbg29_rqBuDczOJ1dgzqGpRacbghfR0OGQhFnKgIXmkGiv_W2EWbo1HcWADc4ClLiq7IEG_EBIc0H6BKKrSitLc1DlwAFDacyr5kC8HBT5PJ5nE8LG9ADQcSgAjlUZoWQGTSo-Z1oe_PzPBXKYNKoUu58YjQ1qylgYIsdFbLD4XJrxR2mKAJBss8CxsysLbmJUKwyimcL9Z9ReJq8AmYTzJJm1Q8vKtVrABsN9hUQaw1MmuTN5NYkKF1HYdvz3QlULLihA18ny5QuxotBKk1yWUBZvGkT5OPc3KZzagsXzE73aqaaXAe20dcTpOn2G5hxyIMKNVv35t0pIHnIS9wQI6lw_o5zL9PAY4y0NHgQqkQLsRvL3tIqN7gfJvcd0Q2BU4fP-9rQGx5kaQJ2gagRJgGWPMEDFc-8i70tvF9H8w2hk-RHmwUzDJXy63a96tnMb_5TWvn8buCOl359ARwgCo3Z8DqDA29hRG8aqXwEpC8qoXOEOJnU5AwbDnEZ8XmPoAd4JicVrPTGspQCYhziHJ-3XbY3fo.PW0tPm0WXGQ-RhQAU4fr7A; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1710687263.355.0.1710687263.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)

    print(time.time() - t)
    pass
