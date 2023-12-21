import asyncio
from functools import wraps

def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper

def templatize_name_id(name, id):
    return f'{name}_[{id}]'