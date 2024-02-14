import json
import os

import requests

from utils.services_utils import lowercase_headers, get_username

api_key = os.getenv('API_KEY')
lang_model_url = os.getenv('LANG_MODEL_URL')


def explain_alternative_plans(plans):
    return (
        f"Given as stringified json, what are the 5 major differences between alternative_plans and original_schedule. "
        f"Key differences would be the largest blocks that were changed from original plan. "
        f"json is {json.dumps(plans)}. "
        f"Explain as a SAAS platform would explain to an OR scheduler. ֿ"
        f"the plaform takes an original schedule and offers an optimized alternative plan that should improve desired metrics such as cost and utilization. "
        f"Don't use the word JSON in your response. "
        f"alternative plan should have higher utilization and potential revenue. "
        f"decreasing the cost as much as possible is desired"
    )


def query_lang_model(content):
    request = {
        "messages": [
            {
                "role": "system",
                "content": content
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "max_tokens": 800,
        "stop": None
    }
    headers = {'api-key': api_key, 'Content-Type': 'application/json'}
    res = requests.post(lang_model_url, json=request, headers=headers, timeout=600)
    return res.json()['choices'][0]['message']['content']


def query_copilot_lambda_handler(event, context):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    method = event['path'].rsplit('/', 1)[-1]
    if method == 'explain-alternative-plans':
        res = query_lang_model(explain_alternative_plans(event['body']))
    elif method == 'explain-block-allocation':
        res = query_lang_model(explain_alternative_plans(event['body']))
    else:
        res = f'method not found: {method}'

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": res
    }


if __name__ == '__main__':
    event = {
        "queryStringParameters": {
            'from': '2024-01-01',
            'to': '2024-01-05'
        },
        'headers': {
            "gmix_serviceid": "hmc-users",
            "referer": 'https://plannerd.greatmix.ai/',
            "Cookie": '_ga=GA1.1.1312836904.1701002261; _ga_TQSJGD3WY1=GS1.1.1701589548.10.1.1701589570.0.0.0; mp_606dec7de8837f2e0819631c0a3066da_mixpanel=%7B%22distinct_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%2C%22%24device_id%22%3A%20%2218d4f587abdc91-04a3f746aa85fc-1f525637-1fa400-18d4f587abe21b6%22%2C%22%24initial_referrer%22%3A%20null%2C%22%24initial_referring_domain%22%3A%20null%2C%22isExtensionEnv%22%3A%20true%2C%22appVersion%22%3A%20%22v2.509.0%22%2C%22source%22%3A%20%22EXTERNAL_TAB%22%2C%22%24current_url%22%3A%20null%2C%22%24referrer%22%3A%20null%2C%22%24referring_domain%22%3A%20null%2C%22%24user_id%22%3A%20%22TycMJ5WSiFQFnmjEy8rxJG%22%7D; _ga_KY8PNQLTFN=GS1.1.1707139038.16.1.1707139109.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNmZkNzVlMC03ZGMzLTQxNDUtOTNlNi1lNTE4YTBiNWIzODUiLCJjb2duaXRvOmdyb3VwcyI6WyJvcG1lZC1zYW5kYm94LTMwLU9ScyIsImhtYy11c2VycyIsIm1heW8tdXNlcnMiLCJvcG1lZC1zYW5kYm94LTIwLU9ScyIsImZoaXItdXNlcnMiLCJvcG1lZC1zYW5kYm94LTUtT1JzIiwibmJpLXVzZXJzIiwib3BtZWQtc2FuZGJveC00MC1PUnMiLCJvcG1lZC1zYW5kYm94LTEwLU9ScyJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwib3JpZ2luX2p0aSI6Ijk4ODhlNWQ1LTQ1YzctNDQyNy1hZTRiLWJmMDE0NTEzMTdlYSIsImV2ZW50X2lkIjoiZTY4ZjYyZTMtODEzOC00YzU1LTg2N2QtYTRmMTY4M2Y1YzAyIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiBwaG9uZSBvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF1dGhfdGltZSI6MTcwNzM5NjEzOSwiZXhwIjoxNzA3NDEwNTM5LCJpYXQiOjE3MDczOTYxMzksImp0aSI6ImRkNmQwYzUwLTk4ZDgtNGQ4NC04NzY5LWM1NTA4YWU0ZjVlOSIsInVzZXJuYW1lIjoibml0emFuQGdyZWF0bWl4LmFpIn0.bGeedIeN1LRpPY46lKcDIkqAYnGTaR2TcZLdADViyZlI9ODwojhU1uBokzI0aREnoeg9-3_QEDH3Rkxx1z0_vBNMFhkYxI7maHMwdpJYhPtQJygMFSM2ak5JIUnqGDZwgVYRXpV-MleeWzNA7cJKKJFq6empoP0vuSRnFrfV2bYIsZCcaAa9wfxPEzo2ps8N-8yYwu0goi_v2O1zdeg0OMvQeds3SS2kqzLia_ciuWzFvucGb2JDsNp1cdk8fB02zmVNrsZNtVyHBodj96cYb0YS5WCKYpnor42_fCrq0Hlgxd9YtodoZvGlmS6fF6CUFI4W83n2OaEZr5jYQ11oZQ; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiNTNyRGZyLTdSQ1RvUnc5dzdhRV8tUSIsInN1YiI6ImE2ZmQ3NWUwLTdkYzMtNDE0NS05M2U2LWU1MThhMGI1YjM4NSIsImNvZ25pdG86Z3JvdXBzIjpbIm9wbWVkLXNhbmRib3gtMzAtT1JzIiwiaG1jLXVzZXJzIiwibWF5by11c2VycyIsIm9wbWVkLXNhbmRib3gtMjAtT1JzIiwiZmhpci11c2VycyIsIm9wbWVkLXNhbmRib3gtNS1PUnMiLCJuYmktdXNlcnMiLCJvcG1lZC1zYW5kYm94LTQwLU9ScyIsIm9wbWVkLXNhbmRib3gtMTAtT1JzIl0sImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJjb2duaXRvOnVzZXJuYW1lIjoibml0emFuQGdyZWF0bWl4LmFpIiwib3JpZ2luX2p0aSI6Ijk4ODhlNWQ1LTQ1YzctNDQyNy1hZTRiLWJmMDE0NTEzMTdlYSIsImNvZ25pdG86cm9sZXMiOlsiYXJuOmF3czppYW06OjI3MzYwNTA5NzIxODpyb2xlXC9jb2duaXRvX2FjY2VzcyJdLCJhdWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwiZXZlbnRfaWQiOiJlNjhmNjJlMy04MTM4LTRjNTUtODY3ZC1hNGYxNjgzZjVjMDIiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTcwNzM5NjEzOSwiZXhwIjoxNzA3NDEwNTM5LCJpYXQiOjE3MDczOTYxMzksImp0aSI6IjEyYWQ1ZmY1LTY5N2QtNDViMi04YzYwLTYwYTNlNjg4NDEzMSIsImVtYWlsIjoibml0emFuQGdyZWF0bWl4LmFpIn0.gkyUg8H0Kndr4ud6M9kaV9SOrx7aSspPX4IHrop2di56whgwaIfn1VthvjOY-j2BkPK4SALsqWagjJnyVavnhrjsLyTP1n0xnGFFdXLOspdaXE0_VNrK9dcqzKeQZwIa3W1VVEmNQPdVo1HLrcIlQoss105MZtAbCOsnE5_w7q2UChH8oahBOM-UuV18FLdgBx6Xlp2dCLHM7Vr-gMfRnYZAbALKyPVgmL-bFr8UoPdvtxTzMKACGzLJncF1qLH265-4WgqP7DJR2BdUdeEauo4Rz1SnLfFOOtUBO8N6GhyOpnGkNK7bvs4ETSXADCAEr131Mm_SCAKk5HiN601WgA; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.Zt54jaz7Xc4i3k_NRVcMhKLQBr_W0LzXwlw7zBRyUXwcBmB8c-hfLI94qwRfAop5vZVBdb3qxUUd0vdRJTrKHQyfZfKS4VlxYCxDXKNUEGdCyyl_cXLD2CLl4ZKB-4B6fHe_wWBHi6fnKQDGvzphChsP7RJySMJ2_IMNYwU6okENWrnA6OivWrCl26eHHHmL1pXBaMLTR53CXY_nF6xWpIx3v8eviU8TbxEbE66drwxH-MKZmj5xY8iC8w-pBYLxV2V9SWIZIrq3kCTH5dkd5kX_ol8Pih5gcaG7vccMHlDiZed4I1UvDDMQI1i18SItqmV8rDpoIy9HYegiJVhOIw.6uq3DD_AQrlkZg4n.TSjn59t_Tq63HyG_sQIrtaryOlzp-0BGvfgawZDihmIaKomqq-c7AE7KIpgCLlVtA57SYOPTdADDSYsbhMEzch09MqfAu71AjLym0l7YwD5l4wN4-1PpNTXcFVMd-EpMUe-aP2jEpNOo3SjQTH6r3Z8Jd-Rf0hTjSNHJgQQb-K7Lw6If_p5aksNedjhNcLt3diX3HnDWPLDxB37epqXKy6C_KhqAssz6MJf1PEk0AqcNto8VS3tZlXb6wZcp9Q5aOvqbukGxt6YENs5MmP09LUH1JxUugbPznb9yjB0o7_CPdRzfEW7lF8leBd9sy5Fe6TXuZ0MtT8_k338qovg5Yuat0RyzZNejHdTP8WjTnzEmeMy2OB9cAdAgTswplnLZpk1fO20VIQQRFZ8sYH57x7YMqcsMYbTdDGRvmeuOuhmUPBJGE8SN8Yv7WpRAqZmKFo7LtBWeib7iC2PfJ3c29tsGxEVZgm18isUysjQKrVyQwySF2_EEGmErBBbGuXPTfvEBNqlPQdDIFWwRfXnpPJQfd1zdCgFHIs5J4XarbkhZYzxke2z7RwPLZdiD1ssoghoK4GH7r1RjkCECnypYmZXCJuBTiDTRRxjV-0Ah4SxhoIsbM1VcSW1P0WMNKayEsmpquKAZiR1U1sQxoKzwpEgVItEakKtLU7Qhc8N-wZYWUW01TsQVkLA7oFCZBU0zdHHgR7H5DATEwqYLNyeTgExtIYTC_TJ7heg7PaWGwo7AQqdEkKok53KgSuaiwvjscQxk2IMaLgXsaMOc1iIyZDGhy6Vj0hllQsZx-Vr5QfqfQ8JZRcVrmoItcQjsPRWgePXmtHQhaNqARqd9cFSYks39kAs7T2WbsGc5Vwc2DsPl3wngCxnvn8ZPv7zkH-cZqc7Z52CVe4pT7VaDolaMFvDg5p6NeCETln3xlFuECFdqDz5K67V2FaJPsWbpEWscmCV-CNBEV8BbJ0PGXbNvdKqQClsA7Jlef-7-v-iB2YnOavCuu_xnSw7mG7D7qR7zoT_gyBumtBLRXAYTKzJhqEeK1hALbPVER8ZjURtewAff1WHAdMlPZ17SVuQJNngIREaw-mVNU7q8TsMpZM_ifeJny1LVDRhomWx6Vo-udolwXIvqVZtSkcQdg-CgZ9E0--AMRJ2oTX0fWH-S1NeXfRyeOysSBX5Risb4C6TbeRAhUjB0vTv6OfLN_Q0Y34W-78bjqVvKNtBCWW-zSYK2t6872EXbusnn6AeCfDvR8cez4qO9mKy6xKGWM1sIUAbfVvk1fK1q1D2DO_DWKOKQjx1a0J2OIAvPxj4oDOF1AIckQ2QQnuqHBjWNtZHEEfCN87hy_Ot9xHBlDkIVzUX6_Ylmsr8OC10.I01QTPkPaNgmWJxqLjXV7Q; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.nitzan%40greatmix.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=nitzan@greatmix.ai; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24device_id%22%3A%20%2218c0ba2af7f227-02a955fde4b537-16525634-1fa400-18c0ba2af7f227%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1707396141.224.0.1707396142.0.0.0'
        }
    }
    proactive_block_realise(event, None)
