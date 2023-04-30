import os
import requests
import time


def get_url():
    return '{}/api/external/fullcalendar_events_ajax'.format(os.environ['HAPROXY_PATH'])


def get_headers():
    headers = {
        "Host": os.environ['HOST'],
        "accept-charset": "utf-8",
        "authorization": os.environ['AUTHORIZATION'],
        "cache-control": "no-cache",
        "content-type": "application/json"
    }
    return headers


def get_data(url, data, headers):
    for i in range(0, 1):
        r = get_data_base(url, data, headers)
        if r is not None:
            return r.json()
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
