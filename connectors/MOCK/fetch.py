from fetch.fake_data import generate_mock_data


def get_url():
    return 'dummy_url'


def get_headers(event):
    headers = {'source': 'mock'}
    return headers


def get_data(url, data, headers):
    return generate_mock_data(4, 10, 3)
