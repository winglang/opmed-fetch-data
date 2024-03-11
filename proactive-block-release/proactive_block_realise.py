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

    return {block['id']: block['releaseStatus'] for block in response['Items']}


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
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.521.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; _ga_KY8PNQLTFN=GS1.1.1709215381.30.0.1709215381.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJmaGlyLXVzZXJzIl0sImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsInZlcnNpb24iOjIsImNsaWVudF9pZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJvcmlnaW5fanRpIjoiNTI2MzNlNzktZjVlZC00MDY4LWEzNWQtODFiMzA0MjViOTcxIiwiZXZlbnRfaWQiOiIzNmM0MDI0My0zM2ZjLTQzNzctODkwZC0yOTU2ZjhlZDI0ZGQiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6ImF3cy5jb2duaXRvLnNpZ25pbi51c2VyLmFkbWluIHBob25lIG9wZW5pZCBwcm9maWxlIGVtYWlsIiwiYXV0aF90aW1lIjoxNzA5NTU4MjQzLCJleHAiOjE3MDk1NzI2NDMsImlhdCI6MTcwOTU1ODI0MywianRpIjoiNWMyY2ZjMjUtNjMyOS00ZDYzLWEzMjktZDY2MmVhMjA3NDBlIiwidXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.Jsy-lq0C9uI44gWiat1Z5qYZMmHbu781fbxXiJpB6b3ZebUCr_mwLRGgdaUAsxuQrm_QDlJou8ahlq0wlh6aRPXYljsk48p4mJgrlUMl1bSKvEqBxx5kyyA6x8dnhITp3pxdbIMWMAZ3ns2-hhuAb_CFuj9UOTHsy7N0UYRu5BgyZv89yxUOA41PxlIhDrBev42PMybuPC6x1ALIhjK99y3G0DvQ_DJk7jNhknv95dfhXjaD0wfbP6PhmGJpp7WzPB9OV23nqQhClo4epz8YzE3NmnhkfA-cO55s98qPztJuaPMYXxYNnnSaZ8iYHx1HAgUqN3We9x3xpV0dB4ny1A; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiRzdaV2U1VGx5eG11MFdXWWtCMVlVQSIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsImZoaXItdXNlcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX1ZIUFJyS2ZFUCIsImNvZ25pdG86dXNlcm5hbWUiOiJuaXR6YW5AZ3JlYXRtaXguYWkiLCJvcmlnaW5fanRpIjoiNTI2MzNlNzktZjVlZC00MDY4LWEzNWQtODFiMzA0MjViOTcxIiwiY29nbml0bzpyb2xlcyI6WyJhcm46YXdzOmlhbTo6MjczNjA1MDk3MjE4OnJvbGVcL2NvZ25pdG9fYWNjZXNzIl0sImF1ZCI6IjM0cmc4ZXN0NWkzNHFuNGtva3QxYzBrdmkiLCJldmVudF9pZCI6IjM2YzQwMjQzLTMzZmMtNDM3Ny04OTBkLTI5NTZmOGVkMjRkZCIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzA5NTU4MjQzLCJleHAiOjE3MDk1NzI2NDMsImlhdCI6MTcwOTU1ODI0MywianRpIjoiZjBlYzYwM2MtYTgwOC00YmE4LWEyODQtODY1YjcxMGU0OTdhIiwiZW1haWwiOiJuaXR6YW5AZ3JlYXRtaXguYWkifQ.OpRIXnNJw-UGuzdjJLCmMflPRBmMua7k2zt_Q1X340pACY-EMxsLmUcFuyP28DV_Gym7NEBXQok1iiM9s5dBLKPPBfWpwJzDqAbyvym-pHinYwAIWaf7V_w_x-Nwy_Uq6JAMM6etLlAM_j6MoV8m6m-OgTLRpLSoMuAgbGgYXTy1468x0wljJPW4Bg0ViN-SwuUUVTXklYgoeK6i6B6LE5oYWpY5GrzI6w6OaLNUYjFc4exHDQjFss3MBaXH8QlGKrO4cGD0D3NRvVPSgpJ3oa1oHGpaxHxWl11jm0UI-udeuBPzKtaNgB-4HFenVnjH203zBi_9JXnzbzWFgklhsA; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.kG3rzylRk-ZMlOs2MZ_rE39YVbnsjXeZ6sznUR19NUpPWD4MEB2l6J7HyZH0Cw3C13tH3EyBtoYQtiSoLYySpU4IBwLUPU3oFTMutLMhRzjLMhF2LYRRFVEL377IKziMddQVdpZ7CHYDPS8pDgf0MDkDMz9VPm3ijh_yDU9_SbYCaN4lA2-GjxINNKkzZEqjY8KcrqCUTGy0FXwjVyd3e6mo_M9afeXCaC8xtop6Z9r9yqY6B2IQ12CxYBA8ohKORvFhY0zh13ujyD-Cl5sRsTWkAG4f3tiJb5RqcOyfH4H1JBoUxDPr45ASaFAPwUq1ZO4OhAEs0P9sejTLxCjYug.rU1iTXrNfAdABS56.pF4RH16mvGvEZJp050OaljTVMRCUS8lVKG6NC9_VAa7hmPIG9mpofdWeBhQ60nUlvZfwT_xjDaae1m-VJsqehiXSBmqhOo9t2u36gg765qpv1w5gF9pwoxUA6ilVMM200-LmlU3jBXr0AoEpy8paVK7pYSOqUaVLaZ8ogvtHoxAW8AIeiYc3QN0xMaEfU7yR4CT9qpC7o79xH4KnKcIrIpXuYs86n8Ew0ivkARiU9S0Z4iSpL5vrqeJ76DEo_5fdvmoit6itHeHDtWGRldJQ91ML6oJxyZtgX-EfrwkwFYLGpsgbjQeQQbjKRZurw5M3RfkWHkTbpeIxvqqZkQ5K7ZXiZ5ON1uRTVCC0-4rnw8G1hU09TkQGWs2hJbPSfbGTGnfvRYewYlqxP6JLejb905bFutDSt4VssiHC0Z7wmqVhkvmdwgm7WoGJB3vXFTJH480rrHmPl_mZoiduX_AHGR0QaHXth7eR_PTI7i_u3JM66KxRKoIQ7JMao7M_ZEok1diU1m1bhYCfwwmxkQHEivu7szluXoCBGce8mtMdCy3HgIICKt6fqYUbCw8g-BiSpnaR-n-qcS9PcvrgKKJIoJWbdKwuzJlqyLlB7Yu6S9gH9SK4mULQYTKXlLE28M34Zd9cl6_2hGtxLnXdurrF0J5J1MGC898iLKg-YV9zx0b_fEpMdEb7suwSFzMn_0b_g3FnIImbVDb7z8gU28qNto1QW7V1mmOdDJ17kGGSjGjn_wWLdvUHWeBT0BjgPleki36qCX7OK7qipcWNXinEM3SmWcPE-P0xSIiPvvIOR24N7maR-1OEYEBfFZLJMlYLQqwebsxzsMpYE6BAWW0gE7jC7EiBd-y9S3xQ-Z5ykWsv5U6UOaaCv1jZXZX7O1zKMZmjyj9qxSQYz9ypnhaD2tBNBMnm19G7JfxEM_j9dygxVIuh3vfBmkGj_4tBFeu1wH5oc6uf0PlpSPU4i1pjQpKA4jDDSiHUk1DuNTVDRIpgl8noB4nwAdIg0aHAB9SSIll238mwlC5m2AO75QVg2X_0eoQeYXtSBvcufA-NYnYAtlfGGGAGUYNcRNB3onlqDPx6o12_EfCVOG3g7qtbW45JS8bJ3RP8tNNGu2BdqJ0O-ofGRY5MArZcBea8j8dEjtP5n75pULJ_JZxXeXcGHaIoX17nSy6RQHeImIUJrDUTAfHJAh0uTGARQMbyMAGxFeWv435XHZvIhCUYDuBaI_asBM-Q5Ron8gOzy6bpxKNNsevXtAN-4HZENUDAZ_cokKEvjzDNBZ9l9PLdvfA0NH2My0fXXgm9WD_4Kc4jzJ0u1G1DxZkMR_Wqfel8dJ2h6wIEQUD6ut1dJxqJ8qecibYlFnEw3Ws.qtm5vgD5OprXhDfrTmFaWw; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1709558244.316.0.1709558244.0.0.0'
        }
    }
    t = time.time()

    res = proactive_block_realise(event, None)
    print(time.time() - t)
    pass
