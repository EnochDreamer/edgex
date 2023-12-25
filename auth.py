from functools import wraps
from flask import abort

def check_permissions(user):
    if (user.admin or user.superuser):
        print('decorated')
        return True
    else:
        abort(401) 



def requires_auth(user):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            check_permissions(user)
            return f(*args, **kwargs)
        return wrapper
    return requires_auth_decorator