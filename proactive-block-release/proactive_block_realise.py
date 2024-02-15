import json
import os
import time
from collections import defaultdict
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests

from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS

url = os.getenv('URL')


def predict_blocks(data_to_predict, headers):
    results = {}
    for key, result in predict_blocks_concurrently(data_to_predict, headers):
        if isinstance(result, Exception):
            raise result
        results[key] = result
    sorted_results = dict(sorted(results.items()))

    return [block for x in sorted_results.values() for block in x.get('blocks', [])]


def predict_blocks_concurrently(data_to_predict, headers):
    with ThreadPoolExecutor(max_workers=30) as executor:
        grouped_blocks = defaultdict(list)
        for block in data_to_predict['blocks']:
            grouped_blocks[datetime.fromisoformat(block['start']).date()].append(block)

        grouped_tasks = defaultdict(list)
        for task in data_to_predict['tasks']:
            grouped_tasks[datetime.fromisoformat(task['start_time']).date()].append(task)

        requests_data_to_send = {}
        for day in grouped_blocks.keys():
            data_to_send = {
                "blocks": grouped_blocks[day],
                "tasks": grouped_tasks[day],
                "metadata": data_to_predict['metadata']
            }
            requests_data_to_send[day] = data_to_send

        future_to_key = {executor.submit(send_predict_request, request_data, headers): day for day, request_data in
                         requests_data_to_send.items()}

        for future in futures.as_completed(future_to_key):
            key = future_to_key[future]
            exception = future.exception()

            if not exception:
                yield key, future.result()
            else:
                yield key, exception


def send_predict_request(data, headers):
    res = requests.post(f'{url}/block-population-risk', json=data, headers=headers)
    if res.status_code != 200:
        print(res.text)
        return {}
    return res.json()


def proactive_block_realise(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    queryStringParameters = {key: val for key, val in event.get('queryStringParameters', {}).items() if
                             key in ['from', 'to']}
    headers = {key: val for key, val in event.get('headers', {}).items() if
               key.lower() in AUTH_HEADERS}

    fetch_data = requests.get(f'{url}/fetch-data/v2', params=queryStringParameters, headers=headers).json()

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

    res = predict_blocks(data_to_predict, headers)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(res)
    }


if __name__ == '__main__':
    event = {
        "queryStringParameters": {
            'from': '2024-02-01',
            'to': '2024-02-05'
        },
        'headers': {
            "gmix_serviceid": "hmc-users",
            "referer": 'https://plannerd.greatmix.ai/',
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.509.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; _ga_KY8PNQLTFN=GS1.1.1707726841.17.0.1707727887.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.pWkXNW1HN6tGyMseilkEHK1tt59BKzBuOmatO7l7IgRpv9jsWMTsJqqiguLIKUYK497cTr3d7zei__E2xiGzVyEpl7ICOsAOEgBsCBjNCM1XWYLO8OQqiIRI_6N7Q9-AMX68Ju8YW2mNmS7TDSyiSqElddD2WoRqsnb16CZQhJ-6mEptyjyVTw48dqTxX_YCAEYWeKcnHbEtEcQUvtfqoB9WtJCqEDdlUWZCo4Bfx8TLwC506GLJrk8fFqOl3s_kGOz-UdQMVMpH9V_hM-FfsnCwjx0C7-Sg0FZRbjykb5zwYExrK4Hwq45ys6TG45b4MKicwGDcAhVk5YAOnxZr5A.781m_rHvg4Bkx-db.CRa432dkK-nU7iNHcS8F2Ksq_QGN3SZcJuQQsGiifVrOEz6AvhMHyC3s_AxPW3c_kRP-w2cSL5_z8uVvVJGNZrTJnnY3VVwxzT9J-mcUP1dEXstsTVNVWvvMN4scEAdiencAoM65CmGrF3hJ7CI5Bg1rJnYqt4C1Cbvg99Qo-JJLwGDlVqjzFdypHxEELnAcdYu_--nperZBJnSCxfX-zDu4ITGaDppKG7Hp-IU5PFzg0Cef2YR0tabMyQW2GZ4zNrIjmSJJ3dWZu8M0gZx85y5yhsXzgX9rKM6Ebb6Jxce67jzqknLe3giKVGXIL5bWhW8D3maMN7tnq1OV1c7vLWQsWnHuwAvoxCHYnX0bha1PevYbeCUTS3eh1j76cuWqaAbddfVenWuukW4pxqW0ILY8fZzK4nFud-hh0UHTwqh8awjrl4LcjmuUeurr_59lhIezF7fcG_iJwwGnd6n6cWnNcm8NWnxXIowCoHVi8ThjEfmJcQqFG84SJ3oihvaox2tjzocAVkuOTlRNCYgNFp5DyBENmE6Q2GvT_jmpwUe6N32bIlJJ9NKurnoy_cQADrlGvB-h5EA_YTxu9Ppm0sqEvU4o0oL1K9JmI_Ni3eXSgTl3Dfv-MV1ONPImTb2oKgj2ZDDY7OpzWbKC9tuTPrhJ_ovMRZHyjetHpGgyuGRveQvOYuSMLuuJMn7hEV4xHoT_mcjtEIvccN6I1H2l2eoc_QJwE_iBhoSDPqsI-oLpu3Tjsns6fTc00L_9Lqn0Gk1RJ0w1D9WMLplKtBiIPRGQxfErP7hxWpmFEmUDBJzW_cbermhJsDu24YEakBIHZOP_gGriyadJTmFsdYt99tujVFieYOv3NSb4_YwdWrpKQAavyF5NyRbkC2Ycoh_LcEztJHfxRC9f--qCNo3bzkvdveLFQkNNXRmWJW8C_Aha1f4jMxKEAcvyEj1yKobumFyB12-xlrJZgC40xOCdPbU97e_muQdsNO6W8CK3udqgDRjdaG-9evXrnch7y8FA5h1c4Pby5SmMgDdxLXOOdbHt2NUj9bO0QhpqvZvLy2dhCU0IevLh9f_jQP0NfugzGB9waq3OOvPn1HC27mYbcWuSwbs-5FqJhIMlVuq-KMwQJX_UHuytPRO_NwvPpgIg75MlYIiNZNiiw88WkAP-T_eJe2J5q5_NgdU51i0vyxr3U_E4Hg3IAI8uOYshHEuRNwcD1zq698zl6b163rC6nQKCVFR1Bm56qhlmZZwb_l5xSEOv-TaOvdt3ISOdIQPuCjFv6_n9aj2iwE8_5tMuiCjcL0p_uWlx4FTICpaMV2zCUVN4acsdA5Zz_b2xN9xFXRGoSMVFtjG0B5443S2G3GoUjXnxwXg.KkLt2aDzSoDYBgUFJtSSYA; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJvcG1lZC1zYW5kYm94LTMwLU9ScyIsImhtYy11c2VycyIsIm1heW8tdXNlcnMiLCJvcG1lZC1zYW5kYm94LTIwLU9ScyIsImZoaXItdXNlcnMiLCJvcG1lZC1zYW5kYm94LTUtT1JzIiwibmJpLXVzZXJzIiwib3BtZWQtc2FuZGJveC00MC1PUnMiLCJvcG1lZC1zYW5kYm94LTEwLU9ScyJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwib3JpZ2luX2p0aSI6Ijg1Y2NiOTYwLTE5OWYtNGM0MC1iOWMxLWNlOGU4MGE1NjE0NyIsImV2ZW50X2lkIjoiNmQ0MWRhNTEtNjE5YS00OTE1LWE4MjMtOGEzZjQ3Zjc5NjIxIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiBwaG9uZSBvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF1dGhfdGltZSI6MTcwNzkyNjUxOCwiZXhwIjoxNzA4MDMxMDM2LCJpYXQiOjE3MDgwMTY2MzYsImp0aSI6IjI4MWM0N2E4LTBiOTItNGQ1MC1iZWUxLTQ5ZGIzYmI3OTFmZCIsInVzZXJuYW1lIjoibml0emFuQGdyZWF0bWl4LmFpIn0.oBQ0xuZIb-HqYXd1c4AK4Q86haWRGoVemQX2-YBRpB_TJ0rIBIoUV6o9HFB1zaQu_Rr-6TgtMngB4um8foObyLGkdME7bznnCHX-vP36MO0o7YOI3MffF8zFyqTZV_VknBqYu1ydN-IaeGIG0bmj2LirBN737jVX0g4e88kzfyPOdhnZF1_sCC_CmqAUdjSkcaEtzPm3r8zrHFfTe-q-GDz_iPxJQpNawx8TywQa8DLvliGeLJ6BAwSdicZmdUgRghykb1QVf6MwioeKv3yGWUAfakAYMXB4kMRyK6nx1FtEYtswraZtWQ079B8yrDrpaDf9jK7vGF5A1wBcEN0M9g; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiZVNxeFFUU0R3ZGZwdWY3TENqbkZGQSIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbIm9wbWVkLXNhbmRib3gtMzAtT1JzIiwiaG1jLXVzZXJzIiwibWF5by11c2VycyIsIm9wbWVkLXNhbmRib3gtMjAtT1JzIiwiZmhpci11c2VycyIsIm9wbWVkLXNhbmRib3gtNS1PUnMiLCJuYmktdXNlcnMiLCJvcG1lZC1zYW5kYm94LTQwLU9ScyIsIm9wbWVkLXNhbmRib3gtMTAtT1JzIl0sImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJjb2duaXRvOnVzZXJuYW1lIjoibml0emFuQGdyZWF0bWl4LmFpIiwib3JpZ2luX2p0aSI6Ijg1Y2NiOTYwLTE5OWYtNGM0MC1iOWMxLWNlOGU4MGE1NjE0NyIsImNvZ25pdG86cm9sZXMiOlsiYXJuOmF3czppYW06OjI3MzYwNTA5NzIxODpyb2xlXC9jb2duaXRvX2FjY2VzcyJdLCJhdWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwiZXZlbnRfaWQiOiI2ZDQxZGE1MS02MTlhLTQ5MTUtYTgyMy04YTNmNDdmNzk2MjEiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTcwNzkyNjUxOCwiZXhwIjoxNzA4MDMxMDM2LCJpYXQiOjE3MDgwMTY2MzYsImp0aSI6IjhlOWFjYmVmLWQzNjktNDU2Yi1iODZhLTczMjdkMWFiNjdhMiIsImVtYWlsIjoibml0emFuQGdyZWF0bWl4LmFpIn0.HGYHNgS-pxzi8b3wnj-6t4ga9N1pa0TmUFmSGZcpudfkdM4SRFzxIxullOo8XJrI5gxLHJsijGj_3V-PEREwTLJN0T2Veha1xepEDAVchMjHZGpNmuaQfvQ6RRxKKApvrasMlil5Cm9W5B2ehQBGr0bfX_LEUrboFd2aeaL2PD0YH6HfA15nCmKpX4kUgGXlJds0tq_jmhiOd_g2i8N6ObibG0LGuDrZyWQo5NCvP_j6LWX8hs0W-rzj_d4axB6imStLS3AA91NUvGsRyX3v-KkU_aZZ_jxJqhRaMeTA-UlreYTIgC4dcOrwlrve5Xa-k1S4DHqxSsUaNtoAQL5Ifg; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1708016637.251.1.1708016652.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)
    print(time.time() - t)
    pass
