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

    fetch_data = requests.get(f'{url}/fetch-data', params=queryStringParameters, headers=event['headers']).json()
    blocks = [x for x in fetch_data if not is_task(x)]
    tasks = [x for x in fetch_data if is_task(x)]

    data_to_predict = {
        'blocks': blocks,
        'tasks': tasks,
        'metadata': {
            "day": "2024-02-06",
            "session_id": "s014a0dd9-2b71-4e6e-acae-ab7491c0ce96xojq4bdOXFoqwEfow5QSmvtwZS7wj",
            "req_id": "req83e026d4-af5f-4b7b-80c1-1cd5e66f0c20g3qYXnqemUGATeRahZDkbTzd2wN",
            "bins": [
                5,
                15,
                30,
                60,
                90
            ],
            "sig_delay": 15,
            "use_ai_predictions": True,
            "min_task_pred_abs": 15,
            "min_task_pred_percent": 0,
            "min_block_pred_abs": 0,
            "min_block_pred_percent": 0,
            "sig_probability": 0.75,
            "request_date_time": 1707232407558,
            "fully_populated_number": 90,
            "parallel_indicator_time": 10,
            "ignored_resource_types": [],
            "parallel_resource_types": [
                "doctor",
                "nurse",
                "nurse",
                "doctor"
            ],
            "overestimated_alert_threshold": 30,
            "underestimated_alert_threshold": 30,
            "daily_risk_factor": 0,
            "ignored_tasks_list": [],
            "ignored_blocks_list": [],
            "constraints": {
                "combined_conditions": [
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_4"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "אב העורקים החזי"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_4"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "AORTOCORONARY BYPASS"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_4"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "AORTIC VALVE REPLACEMENT החלפת מסתם אאורטלי"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_4"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "MITRAL VALVE REPLACEMENT החלפת מסתם מיטרלי"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_7"
                        ],
                        "typeCategory": "EQUIPMENT",
                        "value": "o-arm"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC RADICAL PROSTATECTOMY"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC REIMPLANTATION OF URETER"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC LOBECTOMY LUNG"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC PYELOPLASTY"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC HYSTERECTOMY"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC RADICAL NEPHRECTOMY"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC PARTIAL NEPHRECTOMY"
                    },
                    {
                        "condition": "is_in",
                        "rooms": [
                            "surgery_6"
                        ],
                        "typeCategory": "SURGERY",
                        "value": "ROBOTIC  ASSISTED KNEE REPLACEMENT"
                    }
                ],
                "pinned_blocks": [],
                "devices": {
                    "surgical_tables": 0,
                    "x_ray": 0,
                    "tee": 0,
                    "sterilizers": 0,
                    "blanket_and_fluid_warmers": 0,
                    "monitor": 0,
                    "anesthesia_machines": 0,
                    "hospital_stretchers": 0,
                    "patient_monitors": 0,
                    "defibrillators": 0,
                    "ekg_machines": 0
                },
                "pinned_rooms": [],
                "minimum_beneficial_addon": 60,
                "rooms_to_clear": [],
                "default_settings": {
                    "allow_blocks_shift_from_original": True
                },
                "robot_amount": 10,
                "pacu_anount": 9,
                "staff_members": {
                    "sanitaires": 0,
                    "anesthesiologists": 0,
                    "assistants": 0,
                    "nurses": 0
                },
                "priorities": {
                    "staff_members": 1,
                    "block_shift_from_original": 4,
                    "devices": 1,
                    "free_shift": 3,
                    "generic_add_ons": 5,
                    "rooms_to_clear": 2,
                    "desired_add_ons": 1,
                    "minute_overlap": 5
                },
                "allowed_minutes_per_overlap": 15,
                "add_ons": [],
                "flipped_rooms": [
                    [
                        "surgery_8",
                        "surgery_9"
                    ],
                    [
                        "surgery_1",
                        "surgery_2",
                        "surgery_3",
                        "surgery_4",
                        "surgery_5",
                        "surgery_6",
                        "surgery_7"
                    ]
                ],
                "microscope_amount": 10,
                "weights": {
                    "resilience": 17,
                    "potential_revenue": 17,
                    "cost": 66
                }
            }
        }
    }

    requests.post(f'{url}/block-population-risk', json=data_to_predict, headers=event['headers'])
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
            "Cookie": '_ga=GA1.1.969208942.1695724749; _ga_KY8PNQLTFN=GS1.1.1707138897.9.1.1707140666.0.0.0; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.accessToken=eyJraWQiOiJTcXVEbUZcLzFLY3FEZlFaendDc200ZGNBVU12SldPK3NQK1pkSFRJdUg5VT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzY2FlNDI0NS0wOTI2LTQ1MzMtYWIwMi04NzZlMGI4MGQ0MjMiLCJjb2duaXRvOmdyb3VwcyI6WyJobWMtdXNlcnMiLCJtYXlvLXVzZXJzIiwiZmhpci11c2VycyIsIm5iaS11c2VycyJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzNHJnOGVzdDVpMzRxbjRrb2t0MWMwa3ZpIiwib3JpZ2luX2p0aSI6ImZiNDI5MTE5LWNkZjktNDc0NC04ZWUzLTg1NGMxZGU5ZDk1OCIsImV2ZW50X2lkIjoiOTk2YmE1MDMtZTg2Yi00OGZkLWI4ODYtODVkY2VjNGE4MTNkIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiBwaG9uZSBvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF1dGhfdGltZSI6MTcwNzIyMzQzMSwiZXhwIjoxNzA3MjM3ODMxLCJpYXQiOjE3MDcyMjM0MzEsImp0aSI6IjBmNDBkZDc2LTI1NTQtNGEyOC05MzVmLTE2MTE0ZjA3NmUyNCIsInVzZXJuYW1lIjoib21yaUBvcG1lZC5haSJ9.LhfM6Tu_6E9nNLP8KAgVilMdcuHfZ_HA_IY9AEQQIMiGfvOdfrGcQ7AR4XRE9nNpBBsOZ-PRbK8z9OUv9AxcplyJyf4U1Gji4KveWXJVpEZITiB0Igx5qSbP3JH4DdPeVMOBAjeROAo4Go9bYWQ56hfOqtAGgx00q24ww-6iKNlye49gXuT6AGByMe6cAM_zb-uoaVPi8bcr3HiTMLczSk15i8xWZ6H39B37Zoyv4LqFtXuUCMAZHBFbwlwZRv0w2sFaZfZtuPrAc2M3SjflrhpRNCJ8BvRHKWZAaLwx4FuC1tZ3T38q6yhBxeG5zRlwxjwX-fRr5HrFD-AcCCiwTQ; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.idToken=eyJraWQiOiJhYVdTNm96eGZkaUwxZTczcW9wQVM1dVwvaENCVE5NeWpIRWx4NGNkMXFcL2c9IiwiYWxnIjoiUlMyNTYifQ.eyJhdF9oYXNoIjoiOXM4ZXA3Y1NYMFdiVXJoVW5lLXJCQSIsInN1YiI6IjNjYWU0MjQ1LTA5MjYtNDUzMy1hYjAyLTg3NmUwYjgwZDQyMyIsImNvZ25pdG86Z3JvdXBzIjpbImhtYy11c2VycyIsIm1heW8tdXNlcnMiLCJmaGlyLXVzZXJzIiwibmJpLXVzZXJzIl0sImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9WSFBScktmRVAiLCJjb2duaXRvOnVzZXJuYW1lIjoib21yaUBvcG1lZC5haSIsIm9yaWdpbl9qdGkiOiJmYjQyOTExOS1jZGY5LTQ3NDQtOGVlMy04NTRjMWRlOWQ5NTgiLCJjb2duaXRvOnJvbGVzIjpbImFybjphd3M6aWFtOjoyNzM2MDUwOTcyMTg6cm9sZVwvY29nbml0b19hY2Nlc3MiXSwiYXVkIjoiMzRyZzhlc3Q1aTM0cW40a29rdDFjMGt2aSIsImV2ZW50X2lkIjoiOTk2YmE1MDMtZTg2Yi00OGZkLWI4ODYtODVkY2VjNGE4MTNkIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3MDcyMjM0MzEsImV4cCI6MTcwNzIzNzgzMSwiaWF0IjoxNzA3MjIzNDMxLCJqdGkiOiJjODY2OTQ0MC1jNzMzLTQ3YjgtYjNhOS00OGEyNmIxZmUwYTIiLCJlbWFpbCI6Im9tcmlAb3BtZWQuYWkifQ.YGCXCQOA-GADXK_zlT7dGMdjJX98m6K0S8MZp04vrOQESiWKBFkeuaJyQIhIARC1XawtptA3Afncd1SOHO7py6ubEnsqkOxzFq6v5Ihc7Ijna-hsJZeGa3AiouYaAHrf9WXDppzmjzBDPYAmq8Cb8kVRCdJoOAIsv5zt6Y0-Zk7zh1wGMqVm-LeLClcVJmIVX_HwCojBk1OZ0H5gVJBOj-KlzwOO35cSssyTydT7nUm62uluhM-PMapg4qh2KnW95UZMMSOh9FlGLsIwfcjrHxkZ_U2onZfcUTnH67znoDuVE8FImW95epM451YwH3FtPZ_dxCByVuoka7zQlZsW6Q; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.refreshToken=eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.VQg3aKfjo2yMrWwOsmUbdX7_8fABoN6-1DUu3jNbIscV0v5ZYd7Mha_Ro6yQh1QH8uqx8uxiETIQvuF0Rot5e8tz-XpCZ3so8eNDvjj-Mf4mzwcPWjTPmU73oCNHUwtpeuSF8ju2p84XtsViklMTVHYQABalBxQ3Me2-6RIig-WfChJOshWlrb5plhtmZpdJDrirFucTMUVR4GDZoIhP95S-MR-SGOv50SaxxLTHTmNh3R1qnWlMZ-gAKbv8QsacspiyBI0R5Vb84NE0RgIkUY8CbpxRGuIkUTqmzQAKd_G6B3Arr1dF87PRM2ppJsDSbekSUwJhQOVoPFezS2L_eg.PV9ijgQFBZBJjMmt.-glEtfdQRUozkR9CC-rgM7JKWs1a55Oc8Id8iRv8e-u2RPh5pNJxxkgCqcMmoum_1qo3gLeKTfeCd__5UqLh7tYwWU1Yl8jCfGVsxMKWm7IsLSLXkt_SrxypcjFo91u4Eft2XCnTECN67PC6EDYZvmG5F42VC5kbrd7srdHv7MHay-N6be5bosi3weel-p-bs-1EGu1Dqt37MvYtSE_KOw-Ys8nSc6cMPRLSEfboGnv6D5VO1CpN_i-_3otFcRPYNPppHULj67slM9pUh5ZdxZvpZr-8oKZlXHk96k0BY0fH6LhblWWgyhx5t0-2vWfK99sKdfYjnM7Y3weFqTg1ytj1C--WjrxWvP-TVwX9zgwvjdiVVBlkr9e3tzKM8AOuARRSA2Ei2wFaVNGVtkPaeYYZD1JBDcuy1zfrzyfqBmJaEl8pr7SDy-xkK135NfRAWqg9Jf0HAVhZbvwUVAd52qC_sDLehLltjF7-SBtEzIYI3d9ySWplqNVOlou-CLCHjijtwAaumgBfjDODzF9AWW6_edS-XkGzt_wPmyExldLBeBu3rmasNo-8mwT_pbaF04WON-Ck7D9vKdYk1MISfKSDY8PospZRIDco3AT4SmhajlKjqGvboNFbdeMTrhsA4cjjzAEI1eD2Qp-9mOLXpiBYk09sMK85ZqzBXSot2a8ZS8fExWIk7jwNOb82cfoQMFVdiddjorMDpLaQgs62ZlY5qTl6QPWiL91IOowAs2_j5KwAjYRza75INJNjQHdNlXOcCGHsISm4H1W7GDHM9Rke1RB36lI5v1D-Xo1lP4uD37YTgJ5hNcx2pIGMVQ1H9TMVl-7kBPqLe4i6ICvnOxMMolDu_YGGquXiTiRhU3l-VYEdBobjUy6yfvwFsKW07xGohqytTv76xNGdpPlUs2scvzBtKs_NkSFTLZNOnIamPKEGVfrSs6VhCF9c6RS0y34ZNN_Q1hZbCvICOQ_sUBkW_LIn7JzILHDOWM1e4nXu-K_OErG-R7FWApefLGFQx3j9vR_MpqXKgrBCCPmAEF5TDrCQiNRAcbuifECUtq670us0rSkR0CbkbWLJLUvDlgRt8tyAZzdy5s9k5q6zXRJFsCrCdZ_9cRt2K7wFZsKJnwHik70AogJTrk57K0XmOV60KXEhKKESRvcF0h2C-r8N4Me8vUKTrTw0X_UJAiABjSpk-3dwYT__qnDcZyJAErt2nWPC1_zZyNsfgBH-wJPIwY2sfIJE_iSBzRlqoFmb1ag9qD8f9qkpg8LaiiNOWi4BJOVxUxBJ95WN1xoNu6pw_oeY7lHLRUY-KJZW4AUP6Q7oH9B3lu4ELoDvdYWXAHIgGkoOekA-D4Nz5zFqoA.Uzuw42w64bFIUhTE8wVwZA; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.omri%40opmed.ai.tokenScopesString=phone%20email%20profile%20openid%20aws.cognito.signin.user.admin; CognitoIdentityServiceProvider.34rg8est5i34qn4kokt1c0kvi.LastAuthUser=omri@opmed.ai; mp_66055e6fbec221f1f751c3ea238fafda_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18ad1123ed147-0d7e87ea127c31-18525634-1fa400-18ad1123ed147%22%2C%22%24device_id%22%3A%20%2218ad1123ed147-0d7e87ea127c31-18525634-1fa400-18ad1123ed147%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D; _ga_TQSJGD3WY1=GS1.1.1707231371.99.1.1707232220.0.0.0'
        }
    }
    proactive_block_realise(event, None)
