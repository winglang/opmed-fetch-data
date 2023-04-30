import os
import requests
import time

from utils import convert_dictionary_to_model


def get_url():
    return 'https://plannerd.greatmix.ai/fetch-data'


def get_headers():
    headers = {
        "Cookie": os.environ['COOKIE'],
    }
    return headers


def get_data(url, data, headers):
    for i in range(0, 1):
        r = get_data_base(url, data, headers)
        if r is not None:
            return convert_dictionary_to_model(r.json())
        time.sleep(20)

    return None


def get_data_base(url, data, headers):
    try:
        r = requests.post(url, json=data, headers=headers, verify=False)
        if int(r.status_code) != 200:
            print('ERROR: request error: {} {}'.format(r.text, r.status_code))
            print('ERROR: request request: {}'.format(r))
            print('ERROR: request headers: {}'.format(r.headers))
            return None

        print('request success'.format(r))
        return r
    except Exception as e:
        print('ERROR: request error: {}'.format(e))
        return None
