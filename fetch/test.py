import os
import datetime
import aws_lambda_context

# from fake_data import generate_mock_data
from lambda_function import lambda_handler


def main():
    from_time = datetime.datetime.now()  # - datetime.timedelta(days=2)
    to_time = datetime.datetime.now() + datetime.timedelta(days=1)

    event = {
        "queryStringParameters": {
            "from": from_time.strftime("%Y-%m-%d"),
            "to": to_time.strftime("%Y-%m-%d"),
            "save": False
        },
        "headers": {
            "Cookie": 'CognitoIdentityServiceProvider.34rg8....Copy cookie from browser;'
        }
    }
    context = aws_lambda_context.LambdaContext()

    os.environ['HAPROXY_PATH'] = 'https://plannerd.greatmix.ai'
    os.environ['HOST'] = 'localhost:3000'
    os.environ['AUTHORIZATION'] = 'unit_test'

    # Call the lambda_handler function with the event and context objects
    response = lambda_handler(event, context)

    # Print the response
    # print(response)

    # mockData = generate_mock_data(4, 10, 3)
    # print(mockData)


if __name__ == '__main__':
    main()
