import os
from datetime import timezone, datetime, timedelta

import jwt

algorithm = "HS512"


def generate_401_response():
    return {
        "status": "401",
        "statusDescription": "Unauthorized",
        "headers": {"content-type": [{"key": "Content-Type", "value": "text/plain"}]},
        "body": "Unauthorized: Access is denied due to invalid credentials.",
    }


def generate_403_response():
    return {
        "status": "403",
        "statusDescription": "Forbidden",
        "headers": {"content-type": [{"key": "Content-Type", "value": "text/plain"}]},
        "body": "Forbidden: Access is denied due to lack of permission",
    }


def generate_jwt(tenant_id, user_id, block_ids: str | None = None, symmetric_key=os.getenv("SYMMETRIC_KEY")):
    jwt_expiration_days = float(os.getenv("JWT_EXPIRATION_DAYS", 2))
    expired_at = datetime.now() + timedelta(days=jwt_expiration_days)

    payload = {
        "user_id": user_id,
        "org_id": tenant_id,
        "exp": expired_at.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    }

    if block_ids is not None:
        payload["block_ids"] = block_ids

    encoded_jwt = jwt.encode(payload, symmetric_key, algorithm=algorithm)

    return encoded_jwt


def validate_jwt(token, symmetric_key=os.getenv("SYMMETRIC_KEY")):
    try:
        decoded = jwt.decode(token, symmetric_key, algorithms=[algorithm])
    except Exception as e:
        print(e)
        return False
    return decoded
