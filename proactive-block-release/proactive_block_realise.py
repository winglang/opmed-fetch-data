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

    return {block['data_id']: block['releaseStatus'] for block in response['Items']}


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
            block['releaseStatus'] = blocks_status.get(block['id'], 'new')
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
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.521.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; _ga_KY8PNQLTFN=GS1.1.1710233738.35.0.1710233738.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJmaGlyLXVzZXJzIl0sImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsInZlcnNpb24iOjIsImNsaWVudF9pZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJvcmlnaW5fanRpIjoiOGUzNWJiNDUtM2NjNS00ZmMyLTlmZDgtYThhNGMxOTc5NGFhIiwiZXZlbnRfaWQiOiI2ZmEwMjFiNi00Y2JmLTQzOTgtOWEzZS05ZGFhOTc3NGE3NjYiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6ImF3cy5jb2duaXRvLnNpZ25pbi51c2VyLmFkbWluIHBob25lIG9wZW5pZCBwcm9maWxlIGVtYWlsIiwiYXV0aF90aW1lIjoxNzEwMzIwMDU0LCJleHAiOjE3MTAzMzQ0NTQsImlhdCI6MTcxMDMyMDA1NCwianRpIjoiZjRhNGI1MjYtY2FiMy00OTljLTgyYTMtMjhmMmZjMDNlNDdiIiwidXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.j6IACQnE_0KSUMao8QkFqsssQk203kroQOfRFFVpTQmri1Q7r7lxvNn4n9S0Gdr2ksDHV7cQ0AdrnuSN7znpYHmMXFvLfLqrwZzMgUUTCgr92esUhTAPcjYAXIeVf8tD_axx7mQhuHOYtboi_uqDL0btyKt0X_9Bjqo6lsU3JoxpSjSYvBqOzFyDaNyf0jlxOGeHoo_6sxY1yZGJ34qxvZWHsPLksVfroXhTvTAUxGgdf_QRd7gfQsLu_vuT_lT3wnlBwzHUEmvvI15pFlnIK7biBqw_6APZBwx3ABdYRSBibcq9j_UgvpJl1sOafI8gxJNq925yyc9Vx_FfYUqU5A; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoieXJkRWlYbGFSWG5TV0YzMkEzVGprdyIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsImZoaXItdXNlcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsImNvZ25pdG86dXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkiLCJvcmlnaW5fanRpIjoiOGUzNWJiNDUtM2NjNS00ZmMyLTlmZDgtYThhNGMxOTc5NGFhIiwiY29nbml0bzpyb2xlcyI6WyJhcm46YXdzOmlhbTo6MjczNjA1MDk3MjE4OnJvbGVcL2NvZ25pdG9fYWNjZXNzIl0sImF1ZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJldmVudF9pZCI6IjZmYTAyMWI2LTRjYmYtNDM5OC05YTNlLTlkYWE5Nzc0YTc2NiIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzEwMzIwMDU0LCJleHAiOjE3MTAzMzQ0NTQsImlhdCI6MTcxMDMyMDA1NCwianRpIjoiNDc5NWZiNzUtOTA5ZC00ZmRlLTkxZjctZjJmMGFlZDg3ZDM5IiwiZW1haWwiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.mxaueawHKBDpEQU7Wyj8OlWxSzRO8Z0422DltmoOvFlqmlN_aao_y-IXhZRUtedQG6MphZC6X_SXveryXglGVJzLdLXWDtiJ56RZ7oLfwF1zO6oPHwSVP3nxrRvPuDhCAvwfk8QoUODLy4S5Olyz2I05ptccjihbkW1Rlcy9Z1Ex-KW7-oZFo6bHUBvv3BHtHRRc9yEYxJ3yKg6LPxrduaZrECEvzyZIADjf7iD7mGqqdNnlQhkLI4wUDOTXO4hPmhwhGqBekkTVESFnblBg3FPbu16UMYxxfAZO3njIZyEHZn5QvcaZOwfDNTPLULefWDNXLiDXEUXAgc4pGWzlcw; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.a93lUw31-rsFw8_Rh50iktE_Eb_AVBhela7xP2MBlAPD4FPcGowu9p-gcSoXscw4iW4sV2zl0ZeZlJ9QZuG6_MdgSGHmZJ4vayG3IXs2qXUCipXfNBdJiniO5CbFLoxclObcmR8-bJSIC3kGKrEeUMS_j4p2kwvixmbs0hnYO_ktx8crScrln2GC-kvafsfr_y-XKni03NGsOJVefpg2ZSIuwpFtH8_Z12bKPqzfAIuhiQsYkh-efN8vs-h0Qc3MQJ7AAyHFxHI6hlnbX5gq0WU50KbQGGmH9t5BQmrJ---7Y1EBehxCW2QwjnwgLMFEiz6i5YCRJilrEut1cUxgdQ.c3kwUHN0V0w52swb.r7zgQARD_Ffvrr2TurbQDH4tVwD7DPVPgfJJELrYvt-y8MGOzX9yFhbVv5Uudq7NYvEqTEnzjichSpEredY5wn_0zgNXZD7l5DBmEYpxq9hG8L5NGJrU7nbk6yOktc5XyqpApkejDUS79gVtzKtDWFQcot_oV7ybMJfLfTpBqW8OL389GX8d82rPdgHXEAaommdGozb1KVHv04-d47SAnDTsmzr_f3nOkBTKsRDA033vH-JXPQl-TihzS4zY3TV53LMlFcqIluSo0rZ43UiFVMfvT7yy3WCnrnmZs7t-iWxwDykPFMlQC3D-EbqJdnJ45iKl2C7n5N8tvWuREz5v_cjtYeIpxh-F4-12Eu-V_LPk7tUD9rWrQjaQ-FkbaGI4BIOD8BTvhotHh0Y4hOuCxotUqxsINM5AVjI3RnW1RRTO9xRKhSg0XnaWLrTrVamGN48yoNK8bimMblngtTKrXFggd4gDpW0EQnrGF5NMS7UoNbUpvOEnrlh8osChpezeMwS-SN5RvUvW6BmWOFyWx73UvzZV7r4firn9Fhya0cXmJE1XPDtwShxIvaSjzizMW8DHmiTVU993OEkEYnAGWnscXg-L8aiPRsUY2loIoV0J3q9Q5qD22tBDjz_PfL_oA4EAuAAMUsHkZiFvLvNddmYQmhNLrU2QFNIkpqE1OVCaUZ67z9bTAf2uEZP5jISsyf6xi9f5Qm3hmb4iukmGb-Mjjq8V7Gn40v_zbo7WKHXgku_Pk1tYlw6F7I3DvcZNKGtWYJxdZMPIMUMEGyOYFp8AQ0Av9BK0dsM6lEKkRxbc3Xcm9N3uQILiE3oYhiYeCrOYykAtt56YOPzQSvevhxsEjrjf6eSBqKadi2ZMdNlWfVhr4Uhsccw3BUMSyfLSRbhe7fMIPnPzirawy7xZu_pVwRpyC0BaP9m0b_Q2OCwwcb30r4cBRJJAfGkda8Q8gxFemVa1qpmDwyTn7o3U5tB-OTGT-MRx1lXTnJypFKFHXMdDIrm7AzPcmDmPB7KbEmijFcon8z2KpBqZO64_Xrl1dOYbTGVh3SJR--0-YfriFio65BU0d9HIr8ngPa0oHi5PqaMlo3TuDqT3LovomaHLGIXcHSZuUZwR2hNolfBaq7hToblyXA70CcS2fFThhsfXxaClw30GT9xgrCn8ENyS1NXl9ALACNhmCm2AjNbOCtTS-M-QK3QI90VjYxe5bDcbWlwM-luqgB-i4Ky9DLS4RqeJR9BBCmq_4s-Q-2tSkEqgJbAmKJ5VVr0AeZaQj9kxcD0oqSD1XZXNH9KMuRtAYCjNRkRFeoEAAuHldVfMTC9i73XBc56XQALTmCpIeBKsvkvlSKY0g4thf_XKxK3bIDT8Wcg.ExrZi9DKL_qffrGFkVnFYg; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1710328878.348.1.1710329411.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)
    print(time.time() - t)
    pass
