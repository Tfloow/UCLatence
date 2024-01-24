# Note: argon2 is the pip package 'argon2-cffi'!
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError


# Password hashing and verification ####################################################################################

ph = PasswordHasher()


def hash_password(pwd: str) -> str:
    """
    Return the hashed `pwd` using the argon2 hashing algorithm.

    :param pwd: the password to hash
    :returns the hashed password
    """
    return ph.hash(pwd)


def verify_password(hashed_pwd: str, pwd: str) -> bool:
    """
    Verify that the plaintext `pwd` matches with the hashed password `hashed_pwd` using the argon2 hashing algorithm.

    :param hashed_pwd: a hashed password to compare
    :param pwd: a plaintext password to hash and then compare
    :returns Returns `True` if the password hashes match, `False` if not.
    """
    try:
        ph.verify(hashed_pwd, pwd)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False

########################################################################################################################
