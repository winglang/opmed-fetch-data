import os
from datetime import timezone, datetime, timedelta

import jwt

symmetric_key = os.getenv('SYMMETRIC_KEY')
algorithm = 'HS512'


def generate_jwt(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=2),  # Setting expiration to one day
        "iat": datetime.now(timezone.utc)
    }

    encoded_jwt = jwt.encode(payload, symmetric_key, algorithm=algorithm)

    return encoded_jwt


def validate_jwt(token):
    try:
        decoded = jwt.decode(token, symmetric_key, algorithms=[algorithm])
    except jwt.ExpiredSignatureError:
        return 'expired'
    except jwt.InvalidTokenError:
        return 'invalid'
    return decoded['user_id']
