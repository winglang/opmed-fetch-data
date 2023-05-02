import os
import datetime
import aws_lambda_context

from fake_data import createBlocksAndCases
from lambda_function import lambda_handler


def main():
    two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
    two_weeks_from_now = datetime.datetime.now() + datetime.timedelta(days=14)

    event = {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'cognito:groups': ['fhir-users', 'hmc-users']
                }
            }
        },
        # "body": {
        #     "save": "true"
        # },
        "queryStringParameters": {
            "from": two_days_ago.strftime("%Y-%m-%d"),
            "to": two_weeks_from_now.strftime("%Y-%m-%d"),
            "save": "true"
        }
    }
    context = aws_lambda_context.LambdaContext()

    # os.environ['HAPROXY_PATH'] = 'localhost:3000'
    os.environ['HAPROXY_PATH'] = 'https://plannerd.greatmix.ai'
    os.environ['HOST'] = 'localhost:3000'
    os.environ['AUTHORIZATION'] = 'unit_test'
    os.environ['COOKIE'] = 'CognitoIdentityServiceProvider.34rg8....Copy cookie from browser'

    # Call the lambda_handler function with the event and context objects
    response = lambda_handler(event, context)

    # Print the response
    # print(response)

    # mockData = createBlocksAndCases(10, 3)
    # print(mockData)


if __name__ == '__main__':
    main()
