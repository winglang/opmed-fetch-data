import requests

from utils.services_utils import lowercase_headers, get_username


def proactive_block_realise(event, cotext):
    if lowercase_headers(event):
        return lowercase_headers(event)

    username = get_username(event['headers']['cookie'])

    print(f'username: {username}')

    # today = datetime.date.today()
    # from_date = default_from_date = today - datetime.timedelta(days=3)
    # to_date = default_to_date = today + datetime.timedelta(days=21)
    # save_to_blob = False

    # Unit test only!
    # service = get_service(event)

    queryStringParameters = {key: val for key, val in event.get('queryStringParameters', {}).items() if
                             key in ['from', 'to']}
    url = 'https://plannerd.greatmix.ai'

    fetch_data = requests.get(f'{url}/fetch-data/v2', params=queryStringParameters, headers=event['headers']).json()

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

    # with open('event.json', 'w') as f:
    #     json.dump(data_to_predict, f)

    res = requests.post(f'{url}/block-population-risk', json=data_to_predict, headers=event['headers'])

    pass


if __name__ == '__main__':
    event = {
        "queryStringParameters": {
            'from': '2024-01-01',
            'to': '2024-01-31'
        },
        'headers': {
            "gmix_serviceid": "hmc-users",
            "referer": 'https://plannerd.greatmix.ai/',
            "Cookie": '_ga=GA1.1.969208942.1695724749; _ga_KY8PNQLTFN=GS1.1.1707138897.9.1.1707140666.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzY2FlNDI0NS0wOTI2LTQ1MzMtYWIwMi04NzZlMGI4MGQ0MjMiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJtYXlvLXVzZXJzIiwiZmhpci11c2VycyIsIm5iaS11c2VycyJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwib3JpZ2luX2p0aSI6IjZkOTYwNmJlLTJhZGEtNDdmZC1iZjZlLTRiOGNhZGM2MTk4MiIsImV2ZW50X2lkIjoiNjU2MTM3ZDgtN2ZmZC00ZjRjLTkxYzUtYmRjZDg4MjM2NmNkIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiBwaG9uZSBvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF1dGhfdGltZSI6MTcwNzM3NzEzMSwiZXhwIjoxNzA3MzkxNTMxLCJpYXQiOjE3MDczNzcxMzEsImp0aSI6IjNhN2QxODcyLTdjY2UtNGVmMC05YzI5LTBjZDdiODBmODU0NSIsInVzZXJuYW1lIjoib21yaUBvcG1lZC5haSJ9.jwD0Wb2fmyUcHRj4lojW4LcPdeHHVK4lhCLdVGeRUpWefb7l1lJdyr376Z1IQj9bUvfdzOrr69GyUFkVz_1wT39Qcvh-1WX6PDBd1omAhhSo9P3WalAzi3ITihvze5jK668NKUdcv6g8urNADQwyyokfYiaD8HeuYyXP7SF1ORPk7ClwRP83SBzGQWZmlT3LjIaqpxl8iw-eyuvD_DkqJe5h-2ZzM2wqAiIUE-_2D8joGfkk0OlK9PKZsv7klSxpjMrSJkOBCThiSWHieR5wSofTgX89Cfy0Nfk1faveTSs3tMTIINkdMzYQxaLCU5xmi7aVrs5HoomSIgqJ19Um7g; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiMjBuVkxObXVkUjNjcWdNdjIyeGVLdyIsInN1YiI6IjNjYWU0MjQ1LTA5MjYtNDUzMy1hYjAyLTg3NmUwYjgwZDQyMyIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsIm1heW8tdXNlcnMiLCJmaGlyLXVzZXJzIiwibmJpLXVzZXJzIl0sImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJjb2duaXRvOnVzZXJuYW1lIjoib21yaUBvcG1lZC5haSIsIm9yaWdpbl9qdGkiOiI2ZDk2MDZiZS0yYWRhLTQ3ZmQtYmY2ZS00YjhjYWRjNjE5ODIiLCJjb2duaXRvOnJvbGVzIjpbImFybjphd3M6aWFtOjoyNzM2MDUwOTcyMTg6cm9sZVwvY29nbml0b19hY2Nlc3MiXSwiYXVkIjoiMzRyZzhlc3Q1aTM0cW40a29rdDFjMGt2aSIsImV2ZW50X2lkIjoiNjU2MTM3ZDgtN2ZmZC00ZjRjLTkxYzUtYmRjZDg4MjM2NmNkIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3MDczNzcxMzEsImV4cCI6MTcwNzM5MTUzMSwiaWF0IjoxNzA3Mzc3MTMxLCJqdGkiOiI3NTk4YzdiMy0xM2E2LTQ2ZDYtOTcyYi1lMjBjYWI0ODQzNjIiLCJlbWFpbCI6Im9tcmlAb3BtZWQuYWkifQ.nDf5ijEMiwsM_yp8uL0TlM7jeRtAUOkc8gABmqVzGfuSnlj7fEToGu2L_TWRHsnoQ9Pmrwlh3gjuNmUHHfjOh6rBkatOXJROAfPaL-2m6t9J3wv3RYumgXFGPiyv7RuzeUsYpPAzyps2KkvTrMKGXRQjKwc6uIdm9vZilZHQWmwpNqoIhQlrYTllpbQtMe8zqdPSLe_Yv7H4ZEOGyyHGMqBrkx2jvH3xa5-xb0-x7NoBzGy_2ayZeCW2bHxHaUy0k1GFvOPYkeXSfVcdxNMKg6FCJ0OUA3hsoKApfi4lVn9IppSuVCzYulp0KZeCe-kYBuHorfJGr_g_v7ryxJNHiQ; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.oH-1u715LRG18G2KnKxCksrCx4sRyetOX_g_DmP7Y5XfSWwl5s4c6p3NCEUbGh0SoyEKECfvSLxUZ48s4UpZdXZxDpfXYtQLFBeGvKt8mwgFhbwDo4fAcs_NEc9nAyBf1MIbIkP_TQ3vwMd82rxrAb8GBJuGFj783n4VMQP1VjNdxTysLg6QeRRm2tLAg0Sorr0q2mMO3EdtI_TZGwWJE-fnZ5GPBVrl81N4z_FXHMcEG_FuyCab54XzJhPCbsaLsQkeDGRzdhauMBai6l6apfpxPpiGAPhBCwsRgQXkLaITsx5NoTk-rw7gBtNFV4KP3brR6B1Od_RIlFhaJXnMGQ.Pg7dT9wJbs3ONipg.LwwUT-pcH0rhKWc0-UscJRaIL1oee5Tv1utWS0axHReEjLF_8X1IWryKlvDmlB5s4-6kQzAR5b_bclhtZjQC9-jO62nxEhx7yieXNUPmX6DvTqKvD19uWvZ0e9aabkXQfEdL1aRBnoW-WsnU_drwnyiqLEPU2zlsAifB_hqrrdkxe8B2i042y_kGd0-T-mJuOqxkdea3Kg1mt27TiUylN0BUfN1r50YYg8m6PGp21gQSEcQVf5Xa65lnAfQRcEmhRljcCRX8QNZ3U_awVoDNKZ6gpDi5fPlhGdwol4sKf_kATSRNPfeqF3Z_ujVdys_GSsvnRHfNy5TFDGDhX5e8McMZ4lqUfiAsUc9u1qs3XtIl36oLKRSPYFpvWvvpLEviv7mf1HG7-Tc_AxnGBv4bMGzkxHBs808KwPlRpna8gY2WDrjko3jJo5fDH2oisFuw8hvxvJ1yIfYroeipKS5knw38DX1xjXSoW9fevdHR4JXeM038v6LuQV4ucpEPyQ1v0lHHGNjFZSjdSFnnq5Mtn57xBeeIRED4QbkrQYLKw4w54V0zpJpCKTzLl7V6ZkSgW0CKse1aiplchllS9mwbxjZNTPcep4KuJReIg3jjIf2hDkepWm_3TUwzoe2bVg9bR5PZ51o6Z63nzQSFrY8OFQDW4vGiEU7Pfd8cgFt8l39IQdWqSxYIfrOUG9CCTJ22CiF5N4jVBlQV2nSaIBOxrw6PBTXBiJx-IR2dREfHQ4VtKx2D4xQYGpoALOXr5AnUDBCLTiAW3vJG99ZEReMyMylAUP20F03n47fsOOo0YYFx-19mKuSSTTpjIWE-QH6F2l6i-gq3qDkIwsbzlkRaD4YOwkGO8a1RS-bpX7qJ0dKiX5RujqjAxw7QTCSkkLW2MzQ-W3af4I9rJdFye5kiqApeEYnnpe5_HreCoTkBawz3gOB252iHsNYIy4bJUjvpzF9Z2gdwvmm_4y38jaOCVNox8u_gDAu8Rb7UyzcMU9OnT6e2mnEMrPu-7hq8YYD7zuRsab12l3BzbHu6o-55nB5UCF04urfF7zUsTP5swKt_y4nJJVyiklsxMk3H9tv0LVGKW-Ojr_1KNifCyjg5WiPEde6G7i5M9-kFsprO9Dc95oAEZoRPJBpB-WxoC8QGcR7xEFF3pE9ymLaSsMdfBAyrkhNOjjzSA4mzzhmDR0JDbuwb8-ULXS0_Df7A4ZZeXuCR2iHD66I_LD1JuJneDbgl_DLM5fBR4C6PDM0x6HshbPeWTTsfN-QPr4Mq1kwE8L8wAiuk-Y4a-jpAiQFDyVdVCbRS8hrwAXdTBKXongBRgvT0lLLsXh4sRtxpaYJMSMWp2vdwG_hqvHoXckQihQ.gYGGnDFVpKrWoo3ZUjUVSA; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=omri@opmed.ai; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18ad1123ed147-0d7e87ea127c31-18525634-1fa400-18ad1123ed147%22%2C%22%24device_id%22%3A%20%2218ad1123ed147-0d7e87ea127c31-18525634-1fa400-18ad1123ed147%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga_TQSJGD3WY1=GS1.1.1707379924.107.1.1707379924.0.0.0'
        }
    }
    proactive_block_realise(event, None)
