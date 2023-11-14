import os
from decouple import config

from main.utils import parse_uri_data



PROJECT_NAME = 'analytic_service'
ALLOWED_HOSTS = ['*']
DEBUG = os.environ.get("DEBUG", True)
REDIS_KEYS_EXPIRE = 60 * 60 * 24  # сутки в секундах
SECRET_KEY = os.environ.get("SECRET_KEY", "ldvfoun3i5rVWoiw0erihpog2m3pri4g0354gt4gsdf")

TRUST_TOKEN = os.environ.get("TRUST_TOKEN", "123qweasd")
SENTRY_URL = os.environ.get("SENTRY_URL", "")
LOCAL = "local"
SERVER_ENVIRONMENT = os.environ.get("SERVER_ENVIRONMENT", LOCAL)
IS_LOCAL = SERVER_ENVIRONMENT == LOCAL


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "secret-key"
DEBUG = True
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS").split(" ")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django_clickhouse',
    # "django_extensions",
    # "django_json_widget",
    # "celery",
    # "background_jobs",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
#
# DATABASES = {
#     "default": {
#         "ENGINE": config("SQL_ENGINE", "django.db.backends.postgresql"),
#         "NAME": config("SQL_DATABASE", "main"),
#         "USER": config("SQL_USER", "ma"),
#         "PASSWORD": config("SQL_PASSWORD", ""),
#         "HOST": config("SQL_HOST", "localhost"),
#         "PORT": config("SQL_PORT", "5432"),
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

STATIC_URL = "/django/static/"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

PROJECT_NAME = "main"

KAFKA_URI_MODEL_SIGNAL = os.environ.get(
    "KAFKA_URI_MODEL_SIGNAL", "kafka://none:none@localhost:9092?topic=madirect.analytic"
)
# print('KAFKA_URI_MODEL_SIGNAL =', KAFKA_URI_MODEL_SIGNAL)
kafka_base, kafka_options = parse_uri_data(KAFKA_URI_MODEL_SIGNAL)
KAFKA_HOST = f"{kafka_base.hostname}:{kafka_base.port}"
KAFKA_USERNAME = kafka_base.username
KAFKA_PASSWORD = kafka_base.password
KAFKA_TOPIC = kafka_options.pop("topic")
# print('KAFKA_HOST =', KAFKA_HOST)
# print('KAFKA_USERNAME =', KAFKA_USERNAME)
# print('KAFKA_PASSWORD =', KAFKA_PASSWORD)
# print('KAFKA_TOPIC =', KAFKA_TOPIC)

CLICKHOUSE_URI = config(
    # "CLICKHOUSE_URI", "clickhouse://none:none@localhost:9000/analytic?distributed_ddl_task_timeout=300"
    # "CLICKHOUSE_URI", "clickhouse://:@localhost:9000/analytic?distributed_ddl_task_timeout=300"
    # "CLICKHOUSE_URI", "clickhouse://:@localhost:9000/analytic"
    # "CLICKHOUSE_URI", "tcp://127.0.0.1:9000?debug=true"
    "CLICKHOUSE_URI", "tcp://127.0.0.1:8123/analytic"
    # "CLICKHOUSE_URI", "clickhouse://127.0.0.1:9000/analytic"
    # "CLICKHOUSE_URI", "clickhouse://none:none@localhost:8123/analytic?distributed_ddl_task_timeout=300"
    # "CLICKHOUSE_URI", "clickhouse://:@localhost:8123/analytic?distributed_ddl_task_timeout=300"
)

clickhouse_base, clickhouse_options = parse_uri_data(CLICKHOUSE_URI)
CLICKHOUSE_HOST = clickhouse_base.hostname
CLICKHOUSE_PORT = clickhouse_base.port
CLICKHOUSE_USERNAME = clickhouse_base.username
CLICKHOUSE_PASSWORD = clickhouse_base.password
CLICKHOUSE_DATABASE = clickhouse_base.path[1:]
CLICKHOUSE_OPTIONS = clickhouse_options

__psql_db_uri = "postgresql://postgres:postgres@localhost:5432/analytic"
DATABASE_URI_SAAS = os.environ.get("DATABASE_URI_SAAS", __psql_db_uri)
default_db, default_db_options = parse_uri_data(DATABASE_URI_SAAS)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": default_db.path[1:],
        "USER": default_db.username,
        "PASSWORD": default_db.password,
        "HOST": default_db.hostname,
        "PORT": default_db.port,
        "OPTIONS": default_db_options,
    },
    # 'clickhouse': {
    #     'ENGINE': 'clickhouse_backend.backend',
    #     'NAME': CLICKHOUSE_DATABASE,
    #     'HOST': CLICKHOUSE_HOST,
    #     # 'PORT': CLICKHOUSE_PORT,
    #     'USER': CLICKHOUSE_USERNAME,
    #     'PASSWORD': CLICKHOUSE_PASSWORD,
    #     # 'TEST': {
    #     #     'fake_transaction': True
    #     # }
    # }
}

CLICKHOUSE_DATABASES = {
    # Connection name to refer in using(...) method
    'default': {
        'db_name': CLICKHOUSE_DATABASE,
        'username': CLICKHOUSE_USERNAME,
        'password': CLICKHOUSE_PASSWORD
    }
}

CLICKHOUSE_REDIS_CONFIG = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 11,
    'socket_timeout': 10
}
CLICKHOUSE_CELERY_QUEUE = 'clickhouse'

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'clickhouse_auto_sync': {
        'task': 'django_clickhouse.tasks.clickhouse_auto_sync',
        'schedule': timedelta(seconds=2),  # Every 2 seconds
        'options': {'expires': 1, 'queue': CLICKHOUSE_CELERY_QUEUE}
    }
}


# DATABASE_ROUTERS = ['main.dbrouters.ClickHouseRouter']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ANALYTIC_SERVICE_AUTH_TOKEN = config("ANALYTIC_SERVICE_AUTH_TOKEN", "123qweasd")
SENTRY_URL = config("SENTRY_URL", "")
SERVER_NAME = "analytic_service"
SERVER_ENVIRONMENT = config("SERVER_ENVIRONMENT", "local")
