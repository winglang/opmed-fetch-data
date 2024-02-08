import requests

from fetch.lambda_function import is_task
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
    data_to_predict2test = {
        "metadata": {
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
            },
            "version": "1.0.0"
        },
        "tasks": [
            {
                "sur_name": None,
                "incrementalNumber": 29,
                "operationTypeId": "207",
                "procedure": {
                    "current": [
                        {
                            "side": "Right",
                            "surgery_category": "1002",
                            "surgery_name": "207 > TOTAL KNEE REPLACEMENT",
                            "procedure": "81.54 > TOTAL KNEE REPLACEMENT (T.K.R)",
                            "surgery_duration": "00:30",
                            "procedure_code": "1656253",
                            "procedure_name": "TOTAL KNEE REPLACEMENT (T.K.R)",
                            "procedure_icd": "81.54"
                        }
                    ]
                },
                "resources": [
                    {
                        "id": "1287290375",
                        "group": "anesthetist"
                    },
                    {
                        "id": "1386167781",
                        "group": "nurse"
                    },
                    {
                        "id": "1664965590",
                        "group": "nurse"
                    },
                    {
                        "id": "241438593",
                        "group": "assistant"
                    },
                    {
                        "id": "357083322",
                        "group": "assistant"
                    },
                    {
                        "id": "1651946329",
                        "group": "doctor"
                    },
                    {
                        "id": "1488311407",
                        "group": "room"
                    }
                ],
                "greatmixColor": "doctorColor09",
                "type": "TOTAL KNEE REPLACEMENT",
                "hash_doc_name": "329271385",
                "resourceId": "surgery_9",
                "surgery_id": "237737",
                "parent_block_id": "2286708",
                "id": "237737",
                "end": "2024-02-08T15:00:00",
                "start": "2024-02-08T12:10:00",
                "end_time": "2024-02-08T15:00:00",
                "start_time": "2024-02-08T12:10:00",
                "surgery_category": "1002",
                "surgery_name": "207 > TOTAL KNEE REPLACEMENT",
                "procedure_name": "TOTAL KNEE REPLACEMENT (T.K.R)",
                "procedure_icd": "81.54",
                "patient_age": 77,
                "anesthesia": "y",
                "xray_type_value": None,
                "pacu_min": 90,
                "additionalEquipment": {
                    "monitor": False,
                    "x_ray": False,
                    "hospital_stretchers": False,
                    "defibrillators": False,
                    "anesthesia_machines": False,
                    "patient_monitors": False,
                    "sterilizers": False,
                    "ekg_machines": False,
                    "surgical_tables": False,
                    "blanket_and_fluid_warmers": False,
                    "tee": False,
                    "robot": False,
                    "microscope": False
                },
                "hash_equipment_name": [],
                "duration": 170,
                "predicted_duration": 145,
                "doctor_license": "117024",
                "activity_code": "207",
                "time_allocation_delay": {
                    "end_time": "2024-02-08T14:35:00",
                    "duration": 145,
                    "delay_estimation": 0
                }
            },
            {
                "sur_name": "ד\"ר",
                "incrementalNumber": 87,
                "operationTypeId": "153",
                "procedure": {
                    "current": [
                        {
                            "side": "BIL",
                            "surgery_category": "1001",
                            "surgery_name": "153 > LAP B.S.O",
                            "procedure": "LAPAROSCOPIC SALPINGOOPHORECTOMY BILATERAL",
                            "surgery_duration": "02:00",
                            "procedure_code": None,
                            "procedure_name": None,
                            "procedure_icd": None
                        }
                    ]
                },
                "resources": [
                    {
                        "id": "1654191786",
                        "group": "anesthetist"
                    },
                    {
                        "id": "1042786676",
                        "group": "nurse"
                    },
                    {
                        "id": "995881568",
                        "group": "nurse"
                    },
                    {
                        "id": "1789715113",
                        "group": "assistant"
                    },
                    {
                        "id": "1716859374",
                        "group": "doctor"
                    },
                    {
                        "id": "1488311400",
                        "group": "room"
                    }
                ],
                "greatmixColor": "doctorColor25",
                "type": "LAP B.S.O",
                "hash_doc_name": "1716859374",
                "resourceId": "surgery_2",
                "surgery_id": "241676",
                "parent_block_id": "2321448",
                "id": "241676",
                "end": "2024-02-08T22:00:00",
                "start": "2024-02-08T20:00:00",
                "end_time": "2024-02-08T22:00:00",
                "start_time": "2024-02-08T20:00:00",
                "surgery_category": "1001",
                "surgery_name": "153 > LAP B.S.O",
                "procedure_name": None,
                "procedure_icd": None,
                "patient_age": 50,
                "anesthesia": "y",
                "xray_type_value": None,
                "pacu_min": 45,
                "additionalEquipment": {
                    "monitor": False,
                    "x_ray": False,
                    "hospital_stretchers": False,
                    "defibrillators": False,
                    "anesthesia_machines": False,
                    "patient_monitors": False,
                    "sterilizers": False,
                    "ekg_machines": False,
                    "surgical_tables": False,
                    "blanket_and_fluid_warmers": False,
                    "tee": False,
                    "robot": False,
                    "microscope": False
                },
                "hash_equipment_name": [],
                "duration": 120,
                "predicted_duration": 120,
                "doctor_license": "37622",
                "activity_code": "153",
                "time_allocation_delay": {}
            }
        ],
        "blocks": [
            {
                "start": "2024-02-08T15:00:00",
                "end": "2024-02-08T23:00:00",
                "resourceId": "surgery_9",
                "id": "2274670",
                "hash_title": "349717040",
                "hash_nurse_name": [
                    "90724076",
                    "811972372"
                ],
                "hash_pacu_name": [
                    "1488311407"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1651946329"
                ],
                "hash_anesthetist_name": [
                    "2095755282",
                    "1331025459"
                ],
                "doctor_id": "1263",
                "doctor_name": "",
                "greatmixColor": "doctorColor07",
                "doctors_license": "27437",
                "room": "surgery_9",
                "population_rate": 61,
                "empty_minutes": 185,
                "predicted_population": 0.7958415485965683,
                "predicted_minutes_to_free_up": 98,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 0.7703432986558935,
                "upper_range": 0.8213397985372431,
                "request_days_delta": 14,
                "duration": 480
            },
            {
                "start": "2024-02-08T15:00:00",
                "end": "2024-02-08T21:00:00",
                "resourceId": "surgery_8",
                "id": "2274717",
                "hash_title": "349717040",
                "hash_nurse_name": [
                    "1386167781",
                    "1265429391"
                ],
                "hash_pacu_name": [
                    "1488311406"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "357083322"
                ],
                "hash_anesthetist_name": [
                    "1380831285"
                ],
                "doctor_id": "1263",
                "doctor_name": "",
                "greatmixColor": "doctorColor07",
                "doctors_license": "27437",
                "room": "surgery_8",
                "population_rate": 72,
                "empty_minutes": 100,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 0.997764574984705,
                "probability_to_fully_populate_non_specific": 0.997764574984705,
                "probability_to_fully_populate": 0.997764574984705,
                "lower_range": 0.9672885034481301,
                "upper_range": 1.0327114965518698,
                "request_days_delta": 14,
                "duration": 360
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T15:00:00",
                "resourceId": "surgery_1",
                "id": "2281741",
                "hash_title": "1666158059",
                "hash_nurse_name": [
                    "1845842921",
                    "873997380"
                ],
                "hash_pacu_name": [
                    "1488311399"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1816673842"
                ],
                "hash_anesthetist_name": [
                    "1035601380"
                ],
                "doctor_id": "1526",
                "doctor_name": "",
                "greatmixColor": "doctorColor04",
                "doctors_license": "15311",
                "room": "surgery_1",
                "population_rate": 94,
                "empty_minutes": 30,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 0.9519795543562304,
                "upper_range": 1.0480204456437696,
                "request_days_delta": 14,
                "duration": 480
            },
            {
                "start": "2024-02-08T11:00:00",
                "end": "2024-02-08T21:55:00",
                "resourceId": "surgery_7",
                "id": "2282256",
                "hash_title": "549679651",
                "hash_nurse_name": [
                    "336529825",
                    "558405360"
                ],
                "hash_pacu_name": [
                    "1488311405"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1217536661"
                ],
                "doctor_id": "666",
                "doctor_name": "",
                "greatmixColor": "doctorColor03",
                "doctors_license": "37761",
                "room": "surgery_7",
                "population_rate": 93,
                "empty_minutes": 45,
                "predicted_population": 0.9312977099236641,
                "predicted_minutes_to_free_up": 45,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 0.9312977099236641,
                "upper_range": 0.9312977099236641,
                "request_days_delta": 14,
                "duration": 655
            },
            {
                "start": "2024-02-08T15:00:00",
                "end": "2024-02-08T22:00:00",
                "resourceId": "surgery_1",
                "id": "2282319",
                "hash_title": "2006198300",
                "hash_nurse_name": [
                    "1370265150",
                    "1254051181"
                ],
                "hash_pacu_name": [
                    "1488311399"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1845121354"
                ],
                "hash_anesthetist_name": [
                    "1092784065"
                ],
                "doctor_id": "556",
                "doctor_name": "",
                "greatmixColor": "doctorColor05",
                "doctors_license": "23749",
                "room": "surgery_1",
                "population_rate": 111,
                "empty_minutes": -45,
                "predicted_population": 1.1071428571428572,
                "predicted_minutes_to_free_up": -45,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.1071428571428572,
                "upper_range": 1.1071428571428572,
                "request_days_delta": 14,
                "duration": 420
            },
            {
                "start": "2024-02-08T13:00:00",
                "end": "2024-02-08T22:00:00",
                "resourceId": "surgery_5",
                "id": "2285148",
                "hash_title": "779024218",
                "hash_nurse_name": [
                    "41942278",
                    "987130413"
                ],
                "hash_pacu_name": [
                    "1488311403"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1605859433"
                ],
                "hash_anesthetist_name": [
                    "1809157652"
                ],
                "doctor_id": "1940",
                "doctor_name": "",
                "greatmixColor": "doctorColor12",
                "doctors_license": "22486",
                "room": "surgery_5",
                "population_rate": 99,
                "empty_minutes": 5,
                "predicted_population": 0.9907407407407407,
                "predicted_minutes_to_free_up": 5,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 0.9907407407407407,
                "upper_range": 0.9907407407407407,
                "request_days_delta": 14,
                "duration": 540
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T15:00:00",
                "resourceId": "surgery_8",
                "id": "2286015",
                "hash_title": "1184244893",
                "hash_nurse_name": [
                    "997769471",
                    "553421328"
                ],
                "hash_pacu_name": [
                    "1488311406"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1218981527"
                ],
                "doctor_id": "2528",
                "doctor_name": "",
                "greatmixColor": "doctorColor06",
                "doctors_license": "27203",
                "room": "surgery_8",
                "population_rate": 100,
                "empty_minutes": 0,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 1,
                "upper_range": 1.020528968962632,
                "request_days_delta": 14,
                "duration": 480
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T15:00:00",
                "resourceId": "surgery_9",
                "id": "2286708",
                "hash_title": "329271385",
                "hash_nurse_name": [
                    "1386167781",
                    "1664965590"
                ],
                "hash_pacu_name": [
                    "1488311407"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "241438593",
                    "357083322"
                ],
                "hash_anesthetist_name": [
                    "1287290375"
                ],
                "doctor_id": "2878",
                "doctor_name": "",
                "greatmixColor": "doctorColor09",
                "doctors_license": "117024",
                "room": "surgery_9",
                "population_rate": 106,
                "empty_minutes": -30,
                "predicted_population": 1.0625,
                "predicted_minutes_to_free_up": -30,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.0625,
                "upper_range": 1.0625,
                "request_days_delta": 14,
                "duration": 480
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T13:00:00",
                "resourceId": "surgery_5",
                "id": "2301784",
                "hash_title": "1695355229",
                "hash_nurse_name": [
                    "732204170",
                    "1625455469"
                ],
                "hash_pacu_name": [
                    "1488311403"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "683593946"
                ],
                "doctor_id": "3272",
                "doctor_name": "",
                "greatmixColor": "doctorColor11",
                "doctors_license": "84712",
                "room": "surgery_5",
                "population_rate": 94,
                "empty_minutes": 20,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 0.94,
                "upper_range": 1.0939858883072844,
                "request_days_delta": 14,
                "duration": 360
            },
            {
                "start": "2024-02-08T16:00:00",
                "end": "2024-02-08T22:20:00",
                "resourceId": "surgery_2",
                "id": "2321448",
                "hash_title": "1716859374",
                "hash_nurse_name": [
                    "1042786676",
                    "995881568"
                ],
                "hash_pacu_name": [
                    "1488311400"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1789715113"
                ],
                "hash_anesthetist_name": [
                    "1654191786"
                ],
                "doctor_id": "846",
                "doctor_name": "",
                "greatmixColor": "doctorColor25",
                "doctors_license": "37622",
                "room": "surgery_2",
                "population_rate": 108,
                "empty_minutes": -30,
                "predicted_population": 1.0789473684210527,
                "predicted_minutes_to_free_up": -30,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.0789473684210527,
                "upper_range": 1.0789473684210527,
                "request_days_delta": 14,
                "duration": 380
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T09:00:00",
                "resourceId": "surgery_4",
                "id": "2333827",
                "hash_title": "2084716187",
                "hash_nurse_name": [
                    "1985944139",
                    "1265429391"
                ],
                "hash_pacu_name": [
                    "1488311402"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1789715113"
                ],
                "hash_anesthetist_name": [
                    "1966797869"
                ],
                "doctor_id": "2414",
                "doctor_name": "",
                "greatmixColor": "doctorColor13",
                "doctors_license": "28511",
                "room": "surgery_4",
                "population_rate": 125,
                "empty_minutes": -30,
                "predicted_population": 1.25,
                "predicted_minutes_to_free_up": -30,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.25,
                "upper_range": 1.25,
                "request_days_delta": 14,
                "duration": 120
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T15:00:00",
                "resourceId": "surgery_3",
                "id": "2335405",
                "hash_title": "2144753660",
                "hash_nurse_name": [
                    "910471997",
                    "2052031341"
                ],
                "hash_pacu_name": [
                    "1488311401"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1990543707"
                ],
                "doctor_id": "3161",
                "doctor_name": "",
                "greatmixColor": "doctorColor18",
                "doctors_license": "93613",
                "room": "surgery_3",
                "population_rate": 82,
                "empty_minutes": 85,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 0.7052011331171559,
                "probability_to_fully_populate_non_specific": 0.7052011331171559,
                "probability_to_fully_populate": 0.7052011331171559,
                "lower_range": 0.8863808232959146,
                "upper_range": 1.1136191767040853,
                "request_days_delta": 14,
                "duration": 480
            },
            {
                "start": "2024-02-08T13:00:00",
                "end": "2024-02-08T16:00:00",
                "resourceId": "surgery_2",
                "id": "2349219",
                "hash_title": "291315885",
                "hash_nurse_name": [
                    "311773089",
                    "1097307559"
                ],
                "hash_pacu_name": [
                    "1488311400"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1789715113"
                ],
                "hash_anesthetist_name": [
                    "864700362"
                ],
                "doctor_id": "2249",
                "doctor_name": "",
                "greatmixColor": "doctorColor24",
                "doctors_license": "23824",
                "room": "surgery_2",
                "population_rate": 111,
                "empty_minutes": -20,
                "predicted_population": 1.337131541261926,
                "predicted_minutes_to_free_up": -61,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.2674745742971267,
                "upper_range": 1.4067885082267253,
                "request_days_delta": 14,
                "duration": 180
            },
            {
                "start": "2024-02-08T15:00:00",
                "end": "2024-02-08T18:30:00",
                "resourceId": "surgery_4",
                "id": "2356957",
                "hash_title": "1019207670",
                "hash_nurse_name": [
                    "168273773",
                    "224221904"
                ],
                "hash_pacu_name": [
                    "1488311402"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1966797869"
                ],
                "doctor_id": "2484",
                "doctor_name": "",
                "greatmixColor": "doctorColor16",
                "doctors_license": "19979",
                "room": "surgery_4",
                "population_rate": 110,
                "empty_minutes": -20,
                "predicted_population": 1.0952380952380953,
                "predicted_minutes_to_free_up": -20,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.0952380952380953,
                "upper_range": 1.0952380952380953,
                "request_days_delta": 14,
                "duration": 210
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T15:00:00",
                "resourceId": "surgery_6",
                "id": "2356985",
                "hash_title": "533960615",
                "hash_nurse_name": [
                    "1004315942",
                    "558605561"
                ],
                "hash_pacu_name": [
                    "1488311404"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1086899376"
                ],
                "doctor_id": "3358",
                "doctor_name": "",
                "greatmixColor": "doctorColor20",
                "doctors_license": "120667",
                "room": "surgery_6",
                "population_rate": 94,
                "empty_minutes": 30,
                "predicted_population": 0.9375,
                "predicted_minutes_to_free_up": 30,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 0.9375,
                "upper_range": 0.9375,
                "request_days_delta": 14,
                "duration": 480
            },
            {
                "start": "2024-02-08T15:00:00",
                "end": "2024-02-08T21:00:00",
                "resourceId": "surgery_6",
                "id": "2359787",
                "hash_title": "1599395412",
                "hash_nurse_name": [
                    "1481268883",
                    "732204170"
                ],
                "hash_pacu_name": [
                    "1488311404"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1816673842"
                ],
                "hash_anesthetist_name": [
                    "1287290375"
                ],
                "doctor_id": "2107",
                "doctor_name": "",
                "greatmixColor": "doctorColor21",
                "doctors_license": "29533",
                "room": "surgery_6",
                "population_rate": 94,
                "empty_minutes": 20,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 0.9708789439078727,
                "upper_range": 1.0291210560921273,
                "request_days_delta": 14,
                "duration": 360
            },
            {
                "start": "2024-02-08T14:00:00",
                "end": "2024-02-08T15:00:00",
                "resourceId": "surgery_4",
                "id": "2360965",
                "hash_title": "849080846",
                "hash_nurse_name": [
                    "1985944139",
                    "1265429391"
                ],
                "hash_pacu_name": [
                    "1488311402"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1605859433"
                ],
                "hash_anesthetist_name": [
                    "1966797869"
                ],
                "doctor_id": "2889",
                "doctor_name": "",
                "greatmixColor": "doctorColor15",
                "doctors_license": "37079",
                "room": "surgery_4",
                "population_rate": 100,
                "empty_minutes": 0,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 1,
                "upper_range": 1,
                "request_days_delta": 14,
                "duration": 60
            },
            {
                "start": "2024-02-08T18:30:00",
                "end": "2024-02-08T22:50:00",
                "resourceId": "surgery_4",
                "id": "2361322",
                "hash_title": "1252301535",
                "hash_nurse_name": [
                    "168273773",
                    "224221904"
                ],
                "hash_pacu_name": [
                    "1488311402"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1966797869"
                ],
                "doctor_id": "2832",
                "doctor_name": "",
                "greatmixColor": "doctorColor17",
                "doctors_license": "36806",
                "room": "surgery_4",
                "population_rate": 108,
                "empty_minutes": -20,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": -20,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.08,
                "upper_range": 1.08,
                "request_days_delta": 14,
                "duration": 260
            },
            {
                "start": "2024-02-08T21:00:00",
                "end": "2024-02-08T23:00:00",
                "resourceId": "surgery_6",
                "id": "2361578",
                "hash_title": "1786537998",
                "hash_nurse_name": [
                    "1481268883",
                    "732204170"
                ],
                "hash_pacu_name": [
                    "1488311404"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1287290375"
                ],
                "doctor_id": "129",
                "doctor_name": "",
                "greatmixColor": "doctorColor22",
                "doctors_license": "28148",
                "room": "surgery_6",
                "population_rate": 83,
                "empty_minutes": 20,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 0.8423041994224182,
                "probability_to_fully_populate_non_specific": 0.8423041994224182,
                "probability_to_fully_populate": 0.8423041994224182,
                "lower_range": 0.9256234543850859,
                "upper_range": 1.0743765456149141,
                "request_days_delta": 14,
                "duration": 120
            },
            {
                "start": "2024-02-08T21:00:00",
                "end": "2024-02-08T23:00:00",
                "resourceId": "surgery_8",
                "id": "2361992",
                "hash_title": "1472930366",
                "hash_nurse_name": [
                    "1386167781",
                    "1265429391"
                ],
                "hash_pacu_name": [
                    "1488311406"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1380831285"
                ],
                "doctor_id": "2472",
                "doctor_name": "",
                "greatmixColor": "doctorColor08",
                "doctors_license": "33172",
                "room": "surgery_8",
                "population_rate": 88,
                "empty_minutes": 15,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 0.8729463304516071,
                "probability_to_fully_populate_non_specific": 0.8729463304516071,
                "probability_to_fully_populate": 0.8729463304516071,
                "lower_range": 0.9060843310627004,
                "upper_range": 1.0939156689372995,
                "request_days_delta": 14,
                "duration": 120
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T10:00:00",
                "resourceId": "surgery_7",
                "id": "2362170",
                "hash_title": "915948223",
                "hash_nurse_name": [
                    "130317577",
                    "1115051960"
                ],
                "hash_pacu_name": [
                    "1488311405"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [
                    "1514430749"
                ],
                "hash_anesthetist_name": [
                    "1701298520"
                ],
                "doctor_id": "214",
                "doctor_name": "",
                "greatmixColor": "doctorColor02",
                "doctors_license": "19821",
                "room": "surgery_7",
                "population_rate": 78,
                "empty_minutes": 40,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 0.9621661893209184,
                "probability_to_fully_populate_non_specific": 0.9621661893209184,
                "probability_to_fully_populate": 0.9621661893209184,
                "lower_range": 0.9518445854895137,
                "upper_range": 1.0481554145104863,
                "request_days_delta": 14,
                "duration": 180
            },
            {
                "start": "2024-02-08T07:00:00",
                "end": "2024-02-08T13:00:00",
                "resourceId": "surgery_2",
                "id": "2362179",
                "hash_title": "1327460178",
                "hash_nurse_name": [
                    "311773089",
                    "1097307559"
                ],
                "hash_pacu_name": [
                    "1488311400"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "864700362"
                ],
                "doctor_id": "1914",
                "doctor_name": "",
                "greatmixColor": "doctorColor23",
                "doctors_license": "19692",
                "room": "surgery_2",
                "population_rate": 93,
                "empty_minutes": 25,
                "predicted_population": 0.9305555555555556,
                "predicted_minutes_to_free_up": 25,
                "probability_to_fully_populate_doctor_specific": 1,
                "probability_to_fully_populate_non_specific": 1,
                "probability_to_fully_populate": 1,
                "lower_range": 0.9305555555555556,
                "upper_range": 0.9305555555555556,
                "request_days_delta": 14,
                "duration": 360
            },
            {
                "start": "2024-02-08T09:00:00",
                "end": "2024-02-08T14:00:00",
                "resourceId": "surgery_4",
                "id": "2362180",
                "hash_title": "1279331167",
                "hash_nurse_name": [
                    "1985944139",
                    "1265429391"
                ],
                "hash_pacu_name": [
                    "1488311402"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1966797869"
                ],
                "doctor_id": "2626",
                "doctor_name": "",
                "greatmixColor": "doctorColor14",
                "doctors_license": "27814",
                "room": "surgery_4",
                "population_rate": 77,
                "empty_minutes": 70,
                "predicted_population": 1,
                "predicted_minutes_to_free_up": 0,
                "probability_to_fully_populate_doctor_specific": 0.9463484742846877,
                "probability_to_fully_populate_non_specific": 0.9463484742846877,
                "probability_to_fully_populate": 0.9463484742846877,
                "lower_range": 0.9481754701491883,
                "upper_range": 1.0518245298508118,
                "request_days_delta": 14,
                "duration": 300
            },
            {
                "start": "2024-02-08T15:00:00",
                "end": "2024-02-08T17:00:00",
                "resourceId": "surgery_3",
                "id": "2362181",
                "hash_title": "2002049914",
                "hash_nurse_name": [
                    "910471997",
                    "2052031341"
                ],
                "hash_pacu_name": [
                    "1488311401"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1086899376"
                ],
                "doctor_id": "3312",
                "doctor_name": "",
                "greatmixColor": "doctorColor19",
                "doctors_license": "137754",
                "room": "surgery_3",
                "population_rate": 112,
                "empty_minutes": -15,
                "predicted_population": 1.125,
                "predicted_minutes_to_free_up": -15,
                "probability_to_fully_populate_doctor_specific": 0.01,
                "probability_to_fully_populate_non_specific": 0.01,
                "probability_to_fully_populate": 0.01,
                "lower_range": 1.125,
                "upper_range": 1.125,
                "request_days_delta": 14,
                "duration": 120
            },
            {
                "start": "2024-02-08T06:30:00",
                "end": "2024-02-08T07:00:00",
                "resourceId": "surgery_7",
                "id": "2362185",
                "hash_title": "1534769714",
                "hash_nurse_name": [
                    "gn_14308635"
                ],
                "hash_pacu_name": [
                    "1488311405"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [
                    "1701298520"
                ],
                "doctor_id": "2576",
                "doctor_name": "",
                "greatmixColor": "doctorColor01",
                "doctors_license": "99999",
                "room": "surgery_7",
                "population_rate": 0,
                "empty_minutes": 30,
                "predicted_population": 3.2427260292269366,
                "predicted_minutes_to_free_up": -67,
                "probability_to_fully_populate_doctor_specific": 0.16062822709221009,
                "probability_to_fully_populate_non_specific": 0.16062822709221009,
                "probability_to_fully_populate": 0.16062822709221009,
                "lower_range": 1.7646515184432578,
                "upper_range": 2,
                "request_days_delta": 14,
                "duration": 30
            },
            {
                "start": "2024-02-08T17:00:00",
                "end": "2024-02-08T22:30:00",
                "resourceId": "surgery_3",
                "id": "2362197",
                "hash_title": "1534769714",
                "hash_nurse_name": [
                    "gn_14312479"
                ],
                "hash_pacu_name": [
                    "1488311401"
                ],
                "hash_sanitaire_name": [],
                "hash_assistant_name": [],
                "hash_anesthetist_name": [],
                "doctor_id": "2576",
                "doctor_name": "",
                "greatmixColor": "doctorColor01",
                "doctors_license": "99999",
                "room": "surgery_3",
                "population_rate": 0,
                "empty_minutes": 330,
                "predicted_population": 0.8547266457749614,
                "predicted_minutes_to_free_up": 48,
                "probability_to_fully_populate_doctor_specific": 0.26934964144258905,
                "probability_to_fully_populate_non_specific": 0.26934964144258905,
                "probability_to_fully_populate": 0.26934964144258905,
                "lower_range": 0.7307758727765388,
                "upper_range": 0.9786774187733839,
                "request_days_delta": 14,
                "duration": 330
            }
        ]
    }

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
