import os

from fake_data import generate_mock_data


def get_url():
    return 'https://plannerd.greatmix.ai/fetch-data'


def get_headers():
    headers = {
        "Cookie": os.environ['COOKIE']
    }
    return headers


def get_data(url, data, headers):
    return generate_mock_data(4, 10, 3)
