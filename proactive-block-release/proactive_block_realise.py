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
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.521.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; _ga_KY8PNQLTFN=GS1.1.1710233738.35.0.1710233738.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.AMs1RzObtTH_f7YIh3FSrNr-D_lS9NSy3RtY3IavtVfeNIWpS-7D04sz3vIb9DGu8aWdjPK7HHfCX1H6yJax5mq4vKFjpTEHSgbp9RwxMuoOmNV_JLjyvkElnLZ55J2zcq45azfMF9Y9B_v7-TfeaCxxh35PVxBh_HYOjMRClMLCOS5V3ULeKUYoMIG2xC9T9xq5_0w0BuhcVqk_cE2Sg8YWYeUe5-ntcBuuSvu3c8WqnZgHM8zgU_BxRMRpnV7vJA2hjm3TtA_KzoG-yt9hq9LgKmFZXek9hij_ZyeBDnx8v1aKbN7hEzFRX3GkXbYnHGY7IWV_lgXHkG097UDt2Q.DHxip5XcxENn4191.FjhARKGrFh07vFfmbM62fGcVyS62BhORWDgCpKP89-KGdVWB_YRuyiMfwRFbqPwh1EaDKtTrg262Xnj7CpCAfs8fFN2t-nur4TKfsFgW5VH4RmTCBcxfMgfIBywiOKXxscqluthsqbv6UFsuESOsrE8EDPoVCOTjMFIA6I9YVMsSHoS9Co7IvlLrEYaU5Bhx2uZ4pwVkke5yvvhm1U53SGx1CfbocD_K7si6hEJ34Duy9A4Fl_nCcJwXN6m9_9RrZbTyX2bS6IlEOFO3NebMRYR5zo6iNZNgjHYux0cok9HGc7zNxvn32HQByY5VRl08OXggaXa70b4n3OHVXFGFVDrmS4ix9wT1G8_IDMuiqTaJy8HfCcpOeO68tkGPt5vuOlH0PeJ4cl6g6f_7aJhIwGb6oeZdWdjtRdRDfUlo3Ink3J7ESDa3wOw0xqVp-8i7ndHW9BCZLecSLlboDTwk5Aa3RevJBDo6MnZIIvq8bCI2geemRNIVQ0_6qtWkntj3UoRHD0XdwqgUJ0fs96lhZ_dOpBGI2zCsauoAL9LNX04NJRe_a74WUSoPFkmWU7vwt2nOxgK0sx0TfVhK7q0yaipzSgtLG0aSvqbsyF34BwosoAueYtbrVrwYVeAIzgINWkWPcAltOi6MbClZ__NTj9TQ1wYIr6TlJ872eZjcSTZgkfsJLLooRvpkV7vQlMkcKaOfLFs1r9bNsxt8sK6UkGKZat6hlcXYE-QeA3t3qS_KttG9NS2oEh0oCrE4tFuGwhJPgJKKP_t7KVU-ElPqV758kc8N1QVuaqvxGCZUOE8xzGOaz_bQ-7E7_HK9MsoNQhWRUEg7mHT4mGp8H78otBBVFt3n_VshJz9Zu4iC8pq2NitG4NQq5i_IRk2HfNk2-b--BORfnEI7Tk8tk2ZOW4SQK3WoLaCx4R-RvcU-ANUMzDGksf23q-nCP5U6N-tiBbSlURKOvZLYiiqtAnlO-Q8Un1P9VesuTVbCow8mP1-1DiocHINYcGhcyrMhQnZX4B2bsTdsTG11EeeErB9-ofBByOuUMoBe6h_rnroyU53HV2R2iMpqbUsC3JQNWwg0h9TeUotJ3PDKSu5q6SP8ry8w2UN7b8J5JStTqx60-3Ye6IUT4eVEhsN8UnqjQ3YJMZQ-yj76OQMsXl9Bq9opfZYJ-82CAK6Uy0QiD9OJQVIJO9uxHXDxBwlGj7Ccnz0KgsOn1aNyPh1Gs9nN4A_2IrZ1AXUeZuYB2fZkO7TsNUeh6FuxZ_KuKKquSpkRVI_fdH2m36_ckF6sZhEIwZrLv5Xlz_wXZjIhhwaPm6NJyYI1dcX_e4PHEiNGniuRd8Mo311Sv6ReyaFMfoUl5S0wwSS5-GFr2BY.2tPSIsYzc7LnBfAdxJAk-g; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJmaGlyLXVzZXJzIl0sImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsInZlcnNpb24iOjIsImNsaWVudF9pZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJvcmlnaW5fanRpIjoiMTUyNDBiMDktNGQ3YS00MDRlLWExNmEtZjQ1YmJmNDkyYjBmIiwiZXZlbnRfaWQiOiI2NGNjZjY3Yy1iZjUwLTQyNzgtOGE5ZC1kMTE2YWRlMTBkMGMiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6ImF3cy5jb2duaXRvLnNpZ25pbi51c2VyLmFkbWluIHBob25lIG9wZW5pZCBwcm9maWxlIGVtYWlsIiwiYXV0aF90aW1lIjoxNzEwMzM1ODg2LCJleHAiOjE3MTA0MjgwMTksImlhdCI6MTcxMDQxMzYxOSwianRpIjoiODUxMDFjODQtMDZkNy00ZDQwLTkzOTEtMDRjZmRjMWZiZmIzIiwidXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.Iwb5BAV1hQuq7OJ_oRm9kNil290iAfivHKpuY3UT6A9vEmNHjZx6Mcgo8Nud3zR3z5x9_VBFtndhEUW2Uv5pKVqOpBfITqKYoZt6hRTNs4FzokN6k2SYnlBo9e3Wg6zk9Y-q19wDDLNyOscBKVfABvtS6ZYHhF0JlYyKF9Y66HFTA8FjNKTByJhC6PsESn5-c-oQ0NGOd-spo7NHag0JAD0LSFTajacz4QNWOt9RlNipRPO8snNb1syEla29m0MYdOFCZgasy8xACnZzhI-tzpGvOfAglyLHwk2duGkmtbRplUfsnG1axyMKhC3HHfIG28JZPWa72IwjH9yG3QMvyw; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiX1M5MEJZOUhRTktyc25TNEphUXFBdyIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsImZoaXItdXNlcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsImNvZ25pdG86dXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkiLCJvcmlnaW5fanRpIjoiMTUyNDBiMDktNGQ3YS00MDRlLWExNmEtZjQ1YmJmNDkyYjBmIiwiY29nbml0bzpyb2xlcyI6WyJhcm46YXdzOmlhbTo6MjczNjA1MDk3MjE4OnJvbGVcL2NvZ25pdG9fYWNjZXNzIl0sImF1ZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJldmVudF9pZCI6IjY0Y2NmNjdjLWJmNTAtNDI3OC04YTlkLWQxMTZhZGUxMGQwYyIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzEwMzM1ODg2LCJleHAiOjE3MTA0MjgwMTksImlhdCI6MTcxMDQxMzYxOSwianRpIjoiOThhODlkZjQtN2E1OS00ZTgwLTk1ZDQtY2ZiMmI2ZTZkMjI2IiwiZW1haWwiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.SiSM166-VMUzd16HdcdyqZkIaCKAavAf6Vt5AMm38FS1VJPkWFnT6oUtcYp0NaosiX-AeQqQljp6_k_6HsDPMr26xmmw5D5oVRs_AMgNI5bXRyQp7GVK4eVBHOgDkFgUj5TK2vVmhkRAe1pjT0Zqe3HpgjdbJZYhgYvANDqfN5ZQssoGg8WdTEdO0QR3mK7siGhPGy5gllqE0B9ET7DozakgOv-AQTJCsO_pEITDpm-tkJ8vi_5Vbfttb9Zl-IYu3Weiqp_yBUFGBvl1yzD9a5u7EJ0XEJ_H9fvU_TiegS3DaovZ9KVqWnC9jwpWLNg0FwVVmf4arNxB3CpKUj2oJw; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1710425545.350.1.1710425564.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)
    print(time.time() - t)
    pass
