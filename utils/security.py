import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    return hash_password(plain_pwd) == hashed_pwd