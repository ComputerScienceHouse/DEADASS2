from functools import wraps
from flask import session


def csh_user_auth(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        uid = str(session["userinfo"].get("preferred_username", ""))
        last = str(session["userinfo"].get("family_name", ""))
        first = str(session["userinfo"].get("given_name", ""))
        picture = "https://profiles.csh.rit.edu/image/" + uid
        groups = session["userinfo"].get("groups", [])
        is_eboard = "eboard" in groups
        is_rtp = "rtp" in groups
        auth_dict = {
            "uid": uid,
            "first": first,
            "last": last,
            "picture": picture,
            "admin": is_eboard or is_rtp,
        }
        kwargs["auth_dict"] = auth_dict
        return func(*args, **kwargs)

    return wrapped_function


def latin_to_utf8(string):
    return str(bytes(string, encoding="latin1"), encoding="utf8")


def get_user(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        username = str(session["userinfo"].get("preferred_username", ""))

        user_dict = {
            "username": username
            #'account': account,
            #'student': current_student
        }

        kwargs["user_dict"] = user_dict
        return func(*args, **kwargs)

    return wrapped_function
