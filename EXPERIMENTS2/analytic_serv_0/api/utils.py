from functools import wraps
import django

# Декоратор который чистит соединения к бд чтобы избежать проблем ConnectionAlreadyClosed - у моделей джанго
def ensure_db_connection(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        django.db.close_old_connections()
        result = f(*args, **kwargs)
        return result
    return wrapper