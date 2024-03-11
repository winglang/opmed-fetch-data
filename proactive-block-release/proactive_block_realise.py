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


def get_blocks_status(start, end, tenant):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(blocks_status_table_name)

    response = table.query(
        KeyConditionExpression=Key('tenant_id').eq(tenant),
        FilterExpression=Attr('start').between(start, end)
    )

    return {block['id']: block['status'] for block in response['Items']}


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

    username = get_username(event['headers']['cookie'])

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
            block['status'] = blocks_status.get(block['id'], 'new')
        response_body = json.dumps(predicted_blocks)
    else:
        response_body = blocks_predictions_res.text

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
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.521.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; _ga_KY8PNQLTFN=GS1.1.1709721268.33.1.1709723344.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJmaGlyLXVzZXJzIl0sImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsInZlcnNpb24iOjIsImNsaWVudF9pZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJvcmlnaW5fanRpIjoiOTE5M2QyZmUtOGQ1NC00MzVmLTg3ZTktZjEyODVhZmE4NWExIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiBwaG9uZSBvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF1dGhfdGltZSI6MTcxMDE2NDA3MiwiZXhwIjoxNzEwMTc4NDcyLCJpYXQiOjE3MTAxNjQwNzIsImp0aSI6ImVmODBjYTM2LTg5ODktNDAyZC05ZDIxLTI0MzZiNjVkNTQ1NiIsInVzZXJuYW1lIjoibml0emFuQGdyZWF0bWl4LmFpIn0.OBytMzxdgqljRikcU3TxWZG1fpvlsYL6sPVyXH6kEDnxRRNZ_ElNcRkQHOpBADntQ5FyaL7GXHwHNtyES577Uu9LJfDTnT52TkyOJDj3R7MGzW8ObfwZIS5hotlHsERMGPXGQEdcVxw6irRtH-wZJvaCAfRrICXQmpd0Ac6OB8f9JSBcR15UYScVingDICuvF9w9C48ZrI-UAbgKNlEkYD7MocmYmmCGRvvi03PnCevRF9x9vDbCSziq4wFETkF91rv6_eL_a1kF_46Duxgt8Zwy0IZpI9s4vIv2J3o8OpttZmrg3c1ri0HMK8egjjHJIyclRlxVtLqpiVKTPvLcRg; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoidDlZSXE0MHIxYXhRVW9VUWdXQm81ZyIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsImZoaXItdXNlcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsImNvZ25pdG86dXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkiLCJvcmlnaW5fanRpIjoiOTE5M2QyZmUtOGQ1NC00MzVmLTg3ZTktZjEyODVhZmE4NWExIiwiY29nbml0bzpyb2xlcyI6WyJhcm46YXdzOmlhbTo6MjczNjA1MDk3MjE4OnJvbGVcL2NvZ25pdG9fYWNjZXNzIl0sImF1ZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTcxMDE2NDA3MiwiZXhwIjoxNzEwMTc4NDcyLCJpYXQiOjE3MTAxNjQwNzIsImp0aSI6IjdiYjUzZDYwLTcwNzMtNDA2YS05M2YwLTNjM2ZlY2Q4NzMwZSIsImVtYWlsIjoibml0emFuQGdyZWF0bWl4LmFpIn0.n8ZuyfRBJ4dkSJ1G33CRRDR1HZWrCsaBrJxG2Tad3UQ4VBkfkPBbpEXBFAVICaNQyHNP3BgZUrZj_7q_HASMBtb5rDZHn95DQpL5mlb_HsL_PNUTWls9h3enBmTntR39TgFDb3HtrBDNX__Z-XHg2jWtjYrjtNEdxKXNimI48-KpfCwy9Rm2dA3U7iqKPL7oyN9YzbOb8XvkkwLpww2goauFAEMaxNq5CcK6d9B2BeFB3vniolC2uugcu8DtPdJW5AxFlG8CwEsnjiHlniplPkTXoVVDj8G8TrWf72GFjS1eZnrSWlahpZ6HC5cb9qL8iu5OC4T0YRiPsu-Sztfe5w; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.gl7pyxPnynqwpvOHn4j4J2I6lLGH-Ck5aS7wKaU3NMzbbX0Ub-n-RrK71HFncsyKSveeAx4zXYQE6UJFnPAqKcYgTuSF6f3FaJlmNs6awI_HGxo9OvymrcoGPf9YlNUOaB3zYH31uLTFTxibQRyF_rM5BKEKqzn9hYxCuzyJERj4iTnEQEiunlOhtP2yplCdudmxNqhC7DWCc8HSwAD3KklupQR0WJPb6t9QWVEM2ynFqem3qj5ZZu6VqEixskCLUz6VB6B0xJ5GQpzr8_9-vwxlSLDsPEamvBQY-IxJiPtme6PavjcFW2gBKnP6EUsAeJDHO3w4NI9pG0CybRPtBA.m9CgztZOeRGamf1B.UXEH3d-9AlG7jgwJ-K2Ad9GbW7d8k-1ER40t2k1K3Q30V0Z4fug8I6t144OnNjrfeJfdEHcRI2mgAXpTlV-OWOHmlQjPQqaRiVjfSc-sb9e2VUGCLClnGiG70Peel9elmxMnGgAaNkgBTHb4vRcxjfafXiMJSjrwwAyJF2FUij3IPnwl0OS_WOOt91nct5kpn1B6_63b6BbwWP-AQoZJtON17sbTo2yzqdSn0O6vM1AADpQMteeUaVL3iEapEgBvGRimBsMFrIK_QeukGyg_0KxbiEk35C-FVzo5sQ4HLkqaZxexzH0fF4eyyHzVGxrZrnW3MNHTZ24nX84wTmF1Al6c0hEijve9pJY7wZHBPyqsSCTUaoyq69HQHarPw8WQw1Twhrd8c_lC8fISKfv1WMr5m1EBiYFvZed3Cl0wBcF0j-2tjqHqeH-9bsFQsF94rldxBaeU-xu6-zmsZY9rj8_xDb0NkIDU1Cf6KRRt9HXqN7Z_3_wz--akie5EJSKlj2D8oVI-K7NO29TDR4_me2Mq_770VeNisIzmq4c-o_nprKbeFScHgIT_JVBp7Y6hh7b9PHYNvgrfzOpKLjbMdlwu0ZZPSr8teY5FdbdGIvqXJQH52xI886ZOukdCSGDMMJ6Q2tUwZgnc2K5Cr_h5HJMW5hjv6qkg9q3gW0ZJ9FOA5y9BcbVbwdpKeaQy7C33_4Sx5XLimTRPDqaMXjuknR9JVqqU_tfJHbV8iLHfcXDbxx1tMCud9U2pdDLnhfNLb5PmETU7Z0YlkGHeiW3eLibSqeSXp45fHviiTHFBmlA6oz_TbyShF2WLLSQEFgcTAHZEaYD-9xPLPu6R_pnIjOFNAJRDjHzlYEDMGiA1GTZcsl1HRwIQ-3e8D8JDVeaRwFNf_7STepdYuyeqYXQVnkUPjnRShVy_MDS3k_k2EqyDj0jBl3rICMSLBEME7EMMJkVr4_nwiAisPu2J-TXhHOhS0xM-l91hMQjYWycVTVgWy_ySzclupPbIRfCS1-UghNpvzEFfJ5p_YuKlvl9RecJMSNJx_7XyA0_RHyuY0M3ELpUishPx-FkOVJ3_Q_I5svJYaexq_SI9KUsraPvL71EklhvRNohsecYztpJQzubLA45YtDutfcQ7YS6973WuiQ1oJqLb0naTFaXz-MzxJtC2sJcphoji3q2cjjaedERdRYnpTkbme-cW0vSEaeFLCmHAZ2dibHRJuwbFoZHc8tzkUrIWF9EXyW_zPlznD_hKnCaWlGWPKHFSWvu7LShCueyyyg.UQS3-fW1VcQ-Sp8r57omXA; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1710164073.338.0.1710164074.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)
    print(time.time() - t)
    pass
