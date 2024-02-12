import hashlib


def generate_sha256_hash(data, salt):
    data_with_salt = data + salt
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data_with_salt.encode())
    hashed_string = sha256_hash.hexdigest()
    return hashed_string
