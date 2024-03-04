import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import boto3
import requests
from boto3.dynamodb.conditions import Key

from utils.services_utils import lowercase_headers, get_username, AUTH_HEADERS

url = os.getenv('URL')
blocks_status_table_name = os.getenv('BLOCKS_STATUS_TABLE_NAME')


def get_blocks_status(start, end):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(blocks_status_table_name)

    filter_expression = Key('start').between(start, end)

    response = table.scan(
        FilterExpression=filter_expression
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

    queryStringParameters = {key: val for key, val in event.get('queryStringParameters', {}).items() if
                             key in ['from', 'to']}
    headers = {key: val for key, val in event.get('headers', {}).items() if
               key.lower() in AUTH_HEADERS}

    fetch_data = requests.get(f'{url}/fetch-data/v2', params=queryStringParameters, headers=headers).json()

    with ThreadPoolExecutor() as executor:
        get_blocks_predictions_future = executor.submit(get_blocks_predictions, fetch_data, headers)
        get_blocks_status_future = executor.submit(get_blocks_status, queryStringParameters['from'],
                                                   queryStringParameters['to'])

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
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.521.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.dZRvj-_yFK3RI_XXwJNDGMk_cTX5pTVeeJuZQQAeoehzaRoVG9UPaV946ZVnjLEagqsNRAw7-NalPa6PoxxaA-713NgVFHvf2S8twEVThnimhfq-GuwFMOjh7zt5oRQ3IbngWNrN1AUz9Fpvq1KBcIb15s57BRyd3aYDsGlSFijVHPcJz3TB5wL1eoYUICt0mYWZoGNHvmuZW1sXKBEV4cfatdgRS_rKpAub3JhkxLQMKzNkxPxfWSJvTa8a-9NAp3xd78rABquJNWzjrC8cZImCB-zjSpJjOHG3pzPf7HgAcNCqekaeXfvuWPqGqxkvPTbCBFOJGb6p5UkTl_riZQ.THcL9TnBMDBcrB6N.Yn9RgXDYNkGwTFtOj8OpFy8t3VFnYZ_d5RP6j9-YdFVzDCabUWipFSG6G47IeyNF_Y23g3Kab6n2n7DZm4ch-jKszBI_7kFR0B0bV5Sn4nYHT-P4hMrpVKU0Vr7bOuQOUa7NVWcRhPOavrXGNOnfd1Xyl_FpGJ--BZFSQJ9JKKzqfRikhuJQNrjcuWLskPFWySs0vt0z1Ru5_PoGsD8trg226k8dZnzdv6HHeCI02yjFrDF8fLgsuZxxAzlWGXVLts_9sd2y4xjFHNoOojZlFZbOvPIoUNXJiV0kJ4_ThRS1VyNDYw_ib7SzBYffkfKF_heTf8sdoQe9jnfhMoxzPP6kBrXpjlQZO3foNeOlJ8CogYiTiCYGnbbwfCR6jE-XZa_4IgLXtLq9kSoQPJ-mj74_9Wv0o88Bx9WDLERls6Emu7NXRoYiWe0dPv91BETx0kqfSA2W5eMmsDSTSNCxWTtClRx1DVxm7gqgl7oxbtacStaJzlWlPcqdNyHsGZQUbAD66RElpTRqkRSwwnBxrMKoERQzzS-jsgHRaUsvqpSWp68iRucnFoiKg5Q_9bBF82Nmaa8vsN8iSc89HfmJI7hCbF0Jt-UKY0y7xag78U_2BYDC32--x09pfPo4NghiNV8a2NsF1GwAwjEigFoZA8boWcV_Rm_1z6L8UTWg6_xmNz8_oXFQ0BtofXp3vgxmAKSTXcbzeYLo_VuEo0dlAE8QMM2BZ4fOB8znllTk9ezZLYd_9t3LOOdC17IvZP3TXFcHkZfV3B5HDWOFaRoQNzUsaYfOMacOfW5QHIBdkKttV2OQJRLBhQWXHmimLbLLavtbgdVPjeByqb2deeDiR6mpsVLQXXVtsIQGXLVGgAOLyAP8DpJa14AnKR6zof8Kb_cGZYW1ESVyXt6t-I6P1LRxbXJqECB24vlimKeelyjQ-5mcmcGTcJrq07xYEd0zk4IznTbSN5XQ0p3MWAxmZ6k3NwlW4b-h2yAKdlY8QxMET8iTjEmtaGgq1M6YZ28pA4R71MvZlwmhajf38ZCcPd0DzKPf_vLS46Xa6fs-9_TFPIpr4ku-2z2xyDd1K7TiW2Q0nuZDHhpO-iRBb1S-w3A0rog2PfUP0N88zPRvnicCvwIWUSCJl1dJ2oq-QnTmRL4Y8P8WdlbpkIBMFNWQmeuAl3Vi4y24NOgVKeVcPdvp8MaXuAkQlQPjClz3osQihBNxPA4cHjt5p7LXJTh4iapq_QRFcaQkNS_wX1R35YJHPUxUBZR7TVAJc4QV_M5ot5L45k6s5XAbwxiqeIFawkXRFot3yaMBuaFzIYopmMixA8YxrrvTvK2zNuIvEmwQFgtBW86SOAgxlIzmqkgnXvO3ZQMFMIY.A48XCYFAJYhkJo5gW-u7NQ; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJvcG1lZC1zYW5kYm94LTMwLU9ScyIsImhtYy11c2VycyIsIm1heW8tdXNlcnMiLCJvcG1lZC1zYW5kYm94LTIwLU9ScyIsImZoaXItdXNlcnMiLCJvcG1lZC1zYW5kYm94LTUtT1JzIiwibmJpLXVzZXJzIiwib3BtZWQtc2FuZGJveC00MC1PUnMiLCJvcG1lZC1zYW5kYm94LTEwLU9ScyJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwib3JpZ2luX2p0aSI6IjBjZjk5ZTBiLTM0MWQtNGEwOC04Y2JhLTQ1Njc1NThiMmZlMCIsImV2ZW50X2lkIjoiNmE1MzNhMDMtM2FhMy00OTNkLTliNzAtNDE5M2Y2ZDdjNDQ3IiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiBwaG9uZSBvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF1dGhfdGltZSI6MTcwODg4MTQ0NywiZXhwIjoxNzA4OTQ1OTgzLCJpYXQiOjE3MDg5MzE1ODMsImp0aSI6ImNjNTJmOTMyLTk5YmYtNDc2My04YWEyLTlmYzI5YmEyMWYzNyIsInVzZXJuYW1lIjoibml0emFuQGdyZWF0bWl4LmFpIn0.Mf7WCPg8eROutPG17b3n78tId9mQL4lirthpBIA9_42I2y7zf3EJft98NaywA7JJzzL672S4QQds3jc-Xo1btPULOh0nDZWy-QNpRP1HdGZR3oclhoMotxhL4tB9lE4XInaMMEQzdBh53jxFlY7b0aFO83nVgjfAIhrzNHGM3Q1EovoKNHZF86A3sLdjjO-HfZasIvsuJ4sQ4v_5Ben_P1puY5pjIr5TteURQXJ92DrlA8E9yzdtIRviwEpVMDGyRLE2wHcjN_CoRzM6d6iibQt47JdkqaMetocajCkjocjKabZUGeCjvpmlL8AgeUVefbP2gn94bih0O-Ir4kaXbw; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiZnNyZjk4QzhVWlVGcVV3VG1TTEMtZyIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbIm9wbWVkLXNhbmRib3gtMzAtT1JzIiwiaG1jLXVzZXJzIiwibWF5by11c2VycyIsIm9wbWVkLXNhbmRib3gtMjAtT1JzIiwiZmhpci11c2VycyIsIm9wbWVkLXNhbmRib3gtNS1PUnMiLCJuYmktdXNlcnMiLCJvcG1lZC1zYW5kYm94LTQwLU9ScyIsIm9wbWVkLXNhbmRib3gtMTAtT1JzIl0sImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJjb2duaXRvOnVzZXJuYW1lIjoibml0emFuQGdyZWF0bWl4LmFpIiwib3JpZ2luX2p0aSI6IjBjZjk5ZTBiLTM0MWQtNGEwOC04Y2JhLTQ1Njc1NThiMmZlMCIsImNvZ25pdG86cm9sZXMiOlsiYXJuOmF3czppYW06OjI3MzYwNTA5NzIxODpyb2xlXC9jb2duaXRvX2FjY2VzcyJdLCJhdWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwiZXZlbnRfaWQiOiI2YTUzM2EwMy0zYWEzLTQ5M2QtOWI3MC00MTkzZjZkN2M0NDciLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTcwODg4MTQ0NywiZXhwIjoxNzA4OTQ1OTgzLCJpYXQiOjE3MDg5MzE1ODMsImp0aSI6IjYwZDNiZDZjLTE0ZGYtNDgyMy1hNjIxLTJkMTAyNzkzMmFkMyIsImVtYWlsIjoibml0emFuQGdyZWF0bWl4LmFpIn0.gU3GzYOyOwgVn03-fIaOrMSqsj4QarMzrlSYuvLufRQ6gjKba1tgaNsqa642cC9Is5AzS9CKLZ0VQXS4bXJ4-6SbIX99o82CZG7Io9qf0f0003geoTt9vPkpij3BrYP1gfPYpkRHyOdfSdqCY8nHOx-SsUy527-nYyEGt0SZdsVV_6kPzYQrT12zoUcKAywSJXjDkLv8OymDVqtNHG-0JH6KBRgE8PrAjdAStPn6NY5JKY3-Ew6k4ifYGqE-ujrG5wZq7DrvmMKpHOKTRCOlyTt1y4aCMFOwBtClyN138P9coS7YI8nnZfnShyVFkUBHoL8SjF4UoZK-_Yav_JTDgg; _ga_KY8PNQLTFN=GS1.1.1708931590.24.0.1708931591.0.0.0; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1708934106.287.1.1708934192.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)
    print(time.time() - t)
    pass
