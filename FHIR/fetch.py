import json
import os
import requests
import time

from fake_data import createBlocksAndCases
from utils import convert_dictionary_to_model


def get_url():
    return 'https://plannerd.greatmix.ai/fetch-data'


def get_headers():
    headers = {
        "Cookie": os.environ['COOKIE']
    }
    return headers


def get_data(url, data, headers):
    return createBlocksAndCases(10, 3)
