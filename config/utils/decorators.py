from functools import wraps
def check_pk(f):
    @wraps(f)
    def n(request, *args, **kwargs):
        if 'pk' not in request.auth:
            return 401, {'detail': "Unauthorized"}
        return f(request, *args, **kwargs)
    return n