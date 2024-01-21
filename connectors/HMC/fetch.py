import itertools
import os
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, datetime

import requests

from utils.data_utils import convert_dictionary_to_model


def get_url():
    return '{}/api/external/fullcalendar_events_ajax'.format(os.environ['HAPROXY_PATH'])


def get_headers(event):
    headers = {
        "Host": os.environ['HOST'],
        "accept-charset": "utf-8",
        "authorization": os.environ['AUTHORIZATION'],
        "cache-control": "no-cache",
        "content-type": "application/json"
    }
    return headers


def fetch_all_data_concurrently(url, data, headers, chunk_size=2):
    with ThreadPoolExecutor(max_workers=30) as executor:
        start_date = datetime.strptime(data['start'], "%Y-%m-%d")
        end_data = datetime.strptime(data['end'], "%Y-%m-%d")

        range_chunks = [i for i in range(0, (end_data - start_date).days + chunk_size, chunk_size)]
        range_chunks[-1] = (end_data - start_date).days
        range_chunks = [(start_date + timedelta(days=start), start_date + timedelta(days=end)) for
                        start, end in zip(range_chunks[:-1], range_chunks[1:])]

        requests_data_to_send = []
        for start, end in range_chunks:
            data_to_send = {
                "event_type": data['event_type'],
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            }
            requests_data_to_send += [(url, data_to_send, headers)]
        future_to_key = {
            executor.submit(fetch_request, *request_data): datetime.strptime(request_data[1]['start'], "%Y-%m-%d") for
            request_data in requests_data_to_send}

        for future in futures.as_completed(future_to_key):
            key = future_to_key[future]
            exception = future.exception()

            if not exception:
                yield key, future.result()
            else:
                yield key, exception


def get_data(url, data, headers):
    results = {}
    for key, result in fetch_all_data_concurrently(url=url, data=data, headers=headers):
        if isinstance(result, Exception):
            raise result
        results[key] = result
    sorted_results = dict(sorted(results.items()))

    return list(itertools.chain.from_iterable(sorted_results.values()))


def fetch_request(url, data, headers):
    r = post_request_with_retries(url, data, headers, retries=5)
    if r is not None:
        return convert_dictionary_to_model(r.json())
    print(f'failed to retrieve data for: {data}')
    return []


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


def post_request_with_retries(url, data, headers, retries=5):
    for i in range(retries):
        r = get_data_base(url, data, headers)
        if r is not None:
            return r
