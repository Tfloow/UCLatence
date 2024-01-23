from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()


def hash_password(pwd: str):
    """TODO"""
    return ph.hash(pwd)


def verify_password(hashed_pwd: str, pwd: str):
    try:
        ph.verify(hashed_pwd, pwd)
        return True
    except VerifyMismatchError:
        return False
