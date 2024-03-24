import os
import fcntl
import socket
import struct
import asyncio
import binascii
import warnings
from urllib import parse
from datetime import timedelta
from urllib.parse import urljoin

import django
import sentry_sdk
from django.apps import AppConfig
from django.conf import settings
from kafka_manager.config import Config as KafkaManagerConfig
from django.conf.urls.static import static
from django.conf.global_settings import DATETIME_INPUT_FORMATS
from sentry_sdk.integrations.django import DjangoIntegration

from manage import read_env
from ma_saas.utils.system import ParseLink, parse_uri_data

read_env()

PROJECT_NAME = "MaDirect"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get("SECRET_KEY", "lkmwjenfiuh34hf[82h34[0hf2834yr9283y4rf234f")
DEBUG = int(os.environ.get("DEBUG", default=0))
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CHECK_EMAIL_HOST = os.environ.get("CHECK_EMAIL_HOST", "https://mailcheck.ma.direct")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(" ")

BASE_URL = os.environ.get(
    "BASE_URL", "https://prod.ma.direct"
)  # Используется в случае формирования ссылки без привязки к домену компании

CSRF_TRUSTED_ORIGINS = ["https://dev.ma.direct", "https://stage.ma.direct", "https://pre.ma.direct", "https://ma.direct", BASE_URL]

COMPANY_URL = os.environ.get(
    "COMPANY_URL", "https://{subdomain}.ma.direct"
)  # Используется в случае формирования ссылки с привязкой к домену компании
SERVICE_DOMAIN_SIGN_UP = os.environ.get(
    "SERVICE_DOMAIN_SIGN_UP", "http://127.0.0.1:8000"
)  # Используется для регистрации до появления домена компании (connect.ma.direct)

SERVICE_DOMAIN = os.environ.get("SERVICE_DOMAIN", "127.0.0.1:8000")  # prod.ma.direct # deprecated

INSTALLED_APPS = [
    "nested_admin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "rest_framework",
    "django_fsm",
    "django_filters",
    "simple_history",
    "import_export",
    "generic_relations",
    "django_celery_results",
    "django_celery_beat",
    "accounts.apps.MainConfig",
    "companies.apps.CompaniesConfig",
    "projects.apps.ProjectsConfig",
    "geo_objects.apps.GeoObjectsConfig",
    "dictionaries.apps.DictionariesConfig",
    "tasks.apps.TasksConfig",
    "reports.apps.ReportsConfig",
    "billing.apps.BillingConfig",
    "helpdesk.apps.HelpdeskConfig",
    "data_courier.apps.DataCourierConfig",
    "background.apps.BackgroundConfig",
    "pg_logger.apps.PgLoggerConfig",
    "preferences.apps.PreferencesConfig",
    "system.apps.SystemConfig",
    "tmp.apps.TMPObjectsConfig",
    "django_admin_listfilter_dropdown",
    "autocompletefilter",
    "drf_spectacular",
]

MIDDLEWARE = [
    "ma_saas.middleware.CORSMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "request_logging.middleware.LoggingMiddleware",
    "ma_saas.middleware.RequestMiddleware",
]

ROOT_URLCONF = "ma_saas.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "ma_saas/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "libraries": {},
        },
    },
]

WSGI_APPLICATION = "ma_saas.wsgi.application"

__default_saas_db_uri = "postgresql://postgres:postgres@localhost:5432/saas?sslmode=disable&sslrootcert="
DATABASE_URI_SAAS = os.environ.get("DATABASE_URI_SAAS", __default_saas_db_uri)
saas_db, saas_db_options = parse_uri_data(DATABASE_URI_SAAS)

__default_billing_db_uri = "postgresql://billing:qwe@localhost:5432/billing?sslmode=disable&sslrootcert="
DATABASE_URI_BILLING = os.environ.get("DATABASE_URI_BILLING", __default_billing_db_uri)
billing_db, billing_db_options = parse_uri_data(DATABASE_URI_BILLING)

__default_helpdesk_db_uri = "postgresql://helpdesk:qwe@localhost:5432/helpdesk?sslmode=disable&sslrootcert="
DATABASE_URI_HELPDESK = os.environ.get("DATABASE_URI_HELPDESK", __default_helpdesk_db_uri)
helpdesk_db, helpdesk_db_options = parse_uri_data(DATABASE_URI_HELPDESK)

__default_data_courier_db_uri = (
    "postgresql://data_courier:data_courier@localhost:5432/data_courier?sslmode=disable&sslrootcert="
)
DATABASE_URI_DATA_COURIER = os.environ.get("DATABASE_URI_DATA_COURIER", __default_data_courier_db_uri)
data_courier_db, data_courier_db_options = parse_uri_data(DATABASE_URI_DATA_COURIER)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": saas_db.path[1:],
        "USER": saas_db.username,
        "PASSWORD": saas_db.password,
        "HOST": saas_db.hostname,
        "PORT": saas_db.port,
        "OPTIONS": saas_db_options,
    },
    "billing": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": billing_db.path[1:],
        "USER": billing_db.username,
        "PASSWORD": billing_db.password,
        "HOST": billing_db.hostname,
        "PORT": billing_db.port,
        "OPTIONS": billing_db_options,
    },
    "data_courier": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": data_courier_db.path[1:],
        "USER": data_courier_db.username,
        "PASSWORD": data_courier_db.password,
        "HOST": data_courier_db.hostname,
        "PORT": data_courier_db.port,
        "OPTIONS": data_courier_db_options,
    },
    "helpdesk": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": helpdesk_db.path[1:],
        "USER": helpdesk_db.username,
        "PASSWORD": helpdesk_db.password,
        "HOST": helpdesk_db.hostname,
        "PORT": helpdesk_db.port,
        "OPTIONS": helpdesk_db_options,
    },
}

DATABASE_ROUTERS = ["ma_saas.dbrouters.DbRouter"]

AUTH_PASSWORD_VALIDATORS = [
    # {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = (
    "django.contrib.auth.hashers.BCryptPasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = False
USE_TZ = False

AUTH_USER_MODEL = "accounts.User"

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), "media")
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

DEFAULT_AUTHENTICATION_CLASSES = "DEFAULT_AUTHENTICATION_CLASSES"
DEFAULT_RENDERER_CLASSES = "DEFAULT_RENDERER_CLASSES"
REST_FRAMEWORK = {
    DEFAULT_AUTHENTICATION_CLASSES: ["ma_saas.auth.TokenAuthentication"],
    DEFAULT_RENDERER_CLASSES: [
        "rest_framework.renderers.BrowsableAPIRenderer",
        "ma_saas.json_renderer.UTF8CharsetJSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.DjangoModelPermissions",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    # "DEFAULT_PAGINATION_CLASS": "ma_saas.utils.paginator.CachedPageNumberPagination",
    "DEFAULT_THROTTLE_RATES": {"anon_geocoder": "10/minute"},
}
SPECTACULAR_SETTINGS = {
    "TITLE": "MA DIRECT API",
    "DESCRIPTION": f"""Внутреннее api для разработчиков сервисов.
    См также
    \n    {urljoin(BASE_URL, 'api/v1')}
    \n    {urljoin(BASE_URL, 'swagger/')}
    \n    {urljoin(BASE_URL, 'redoc/')}
    \n Для более удобного пользования полезно изучить программу `Postman` и команду `curl`
    """,
    "VERSION": "1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "\/api\/v1\/",
}


# if DEBUG:
#     REST_FRAMEWORK[DEFAULT_RENDERER_CLASSES].insert(0, "rest_framework.renderers.BrowsableAPIRenderer")
# SWAGGER_SETTINGS = {
#     "SECURITY_DEFINITIONS": {"DRF Token": {"type": "apiKey", "name": "Authorization", "in": "header"}},
# }

LOG_PATH = os.path.join(BASE_DIR, "proxy/pg_logger/views").replace("/", ".")
CONSOLE_LOGGER = "*"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[DJANGO] %(levelname)s %(asctime)s %(module)s "
            "%(name)s.%(funcName)s:%(lineno)s: %(message)s"
        },
    },
    "handlers": {
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "default"},
        "serv_logger": {
            "level": "DEBUG",
            "class": "ma_saas.server_logger.ServLoggerHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "ServerLogger": {"handlers": ["serv_logger"], "level": "DEBUG", "propagate": True},
        CONSOLE_LOGGER: {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        "*": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
    },
}

BILLING_HOST = os.environ.get("BILLING_HOST", "localhost:9090")
# realm_if for every project and system is uniq, fro saas dev instance is 1
REALM_ID = os.environ.get("REALM_ID", 1)

MEDIA_STORE_LINK = os.environ.get(
    "MEDIA_STORE",
    "localhost:10999?"
    "ID_REQUEST_HOST=http://123.millionagents.com&"
    "MEDIA_SECRET_KEY=0e83c8a58b9c0ba01f875f3d93d54e48&"
    "PUBLIC_LINK_SECRET_KEY=e0913df826d9a8560a9d5acacad6602d",
)
MediaStoreLink = ParseLink(MEDIA_STORE_LINK)
MEDIA_STORE = MediaStoreLink.url_path
MEDIA_STORE_ID_REQUEST_HOST = MediaStoreLink.options.get("ID_REQUEST_HOST")
MEDIA_SECRET_KEY = binascii.unhexlify(MediaStoreLink.options.get("MEDIA_SECRET_KEY"))
PUBLIC_LINK_SECRET_KEY = binascii.unhexlify(MediaStoreLink.options.get("PUBLIC_LINK_SECRET_KEY"))

MEDIA_STORE_GET_OBJ_LINK = urljoin(MEDIA_STORE, "api/v1/get/{}")

# local (на локальной машине)
# test (возможно метсто, где прогоняются тесты)
# dev (development, первая инстанция для разрабов)
# stage (для тестировщиков)
# prod (production)
LOCAL, PRODUCTION, DEV, STAGE = "local", "prod", "dev", "stage"
SERVER_ENVIRONMENT = os.environ.get("SERVER_ENVIRONMENT", LOCAL)

SERVICE_INSTANCE = "_".join([PROJECT_NAME, SERVER_ENVIRONMENT])

IS_LOCAL_SERVER = SERVER_ENVIRONMENT == LOCAL or SERVER_ENVIRONMENT.endswith(f"_{LOCAL}")
IS_PRODUCTION_SERVER = SERVER_ENVIRONMENT == PRODUCTION or SERVER_ENVIRONMENT.endswith(PRODUCTION)
IS_DEVELOPMENT_SERVER = SERVER_ENVIRONMENT == DEV or SERVER_ENVIRONMENT.endswith(DEV)
IS_STAGE_SERVER = SERVER_ENVIRONMENT == STAGE or SERVER_ENVIRONMENT.endswith(STAGE)
if not IS_LOCAL_SERVER:
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_URL", ""),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        environment=SERVER_ENVIRONMENT,
        send_default_pii=True,
    )

LOCAL_AUTHENTICATION = IS_LOCAL_SERVER or SERVER_ENVIRONMENT == PRODUCTION

ANALYTIC_LINK = os.environ.get("ANALYTIC_SERVICE", "http://127.0.0.1:8013?AUTH_TOKEN=123qweasd")
AnalyticLink = ParseLink(ANALYTIC_LINK)
ANALYTIC_HOST = AnalyticLink.url_path
ANALYTIC_AUTH_TOKEN = AnalyticLink.options.get("AUTH_TOKEN")

DOCSHUB_LINK = os.environ.get("DOCSHUB", "")
DocshubLink = ParseLink(DOCSHUB_LINK)
DOCSHUB_HOST = DocshubLink.url_path
DOCSHUB_AUTH_TOKEN = DocshubLink.options.get("AUTH_TOKEN")

REALMROUTERSERV_LINK = os.environ.get("REALMROUTERSERV", "")
RealmRouteLink = ParseLink(REALMROUTERSERV_LINK)
REALMROUTERSERV_HOST = RealmRouteLink.url_path
REALMROUTERSERV_AUTH_TOKEN = RealmRouteLink.options.get("AUTH_TOKEN")

REQUISITES_LINK = os.environ.get("REQUISITES", "")  # банковские реквизиты
RequisitesLink = ParseLink(REQUISITES_LINK)
REQUISITES_HOST = RequisitesLink.url_path
REQUISITES_AUTH_TOKEN = RequisitesLink.options.get("AUTH_TOKEN")

FILE_UPLOADER_LINK = os.environ.get("FILE_UPLOADER", "127.0.0.1:8003?AUTH_TOKEN=123qweasd")
FileUploaderLink = ParseLink(FILE_UPLOADER_LINK)
FILE_UPLOADER_HOST = FileUploaderLink.url_path
FILE_UPLOADER_TOKEN = FileUploaderLink.options["AUTH_TOKEN"]

uri_db, _ = parse_uri_data(os.environ.get("REDIS_URI_POLICIES", "redis://localhost:6379/0"))
REDIS_HOST, REDIS_PORT, REDIS_DATABASE = uri_db.hostname, uri_db.port, int(uri_db.path[1:])

BROKER_URL = os.environ.get("CELERY_BROKER_URI", "redis://localhost:6379/1")
CELERY_QUEUE = os.environ.get("CELERY_QUEUE", "madirect_backgrounds")

POLICIESSERV_LINK = os.environ.get("POLICIESSERV", "http://127.0.0.1:8002?AUTH_TOKEN=123qweasd")
PoliciesServLink = ParseLink(POLICIESSERV_LINK)
POLICIESSERV_HOST = PoliciesServLink.url_path
POLICIESSERV_TOKEN = PoliciesServLink.options["AUTH_TOKEN"]

RATESSERV_LINK = os.environ.get("RATESSERV", "http://127.0.0.1:8002?AUTH_TOKEN=123qweasd")
RatesServLink = ParseLink(RATESSERV_LINK)
RATESSERV_HOST = RatesServLink.url_path
RATESSERV_TOKEN = RatesServLink.options["AUTH_TOKEN"]

HELPDESK_LINK = os.environ.get("HELPDESK", "http://127.0.0.1:8002?AUTH_TOKEN=123qweasd")
HelpdeskLink = ParseLink(HELPDESK_LINK)
HELPDESK_HOST = HelpdeskLink.url_path
HELPDESK_TOKEN = HelpdeskLink.options["AUTH_TOKEN"]

MESSENGER_LINK = os.environ.get("MESSENGER", "http://127.0.0.1:4000?AUTH_TOKEN=123")
MessengerLink = ParseLink(MESSENGER_LINK)
MESSENGER_HOST = MessengerLink.url_path
MESSENGER_TOKEN = MessengerLink.options["AUTH_TOKEN"]

TOKEN_FOR_EXTERNAL_SERVICE = os.environ.get("TOKEN_FOR_EXTERNAL_SERVICE", "TOKEN")

YANDEX_GEOCODER_API_KEY = os.environ.get("YANDEX_GEOCODER_API_KEY", "")

KAFKA_URI = os.environ.get("KAFKA_URI", "kafka://none:none@localhost")
kafka, _ = parse_uri_data(KAFKA_URI)
kafka_host = kafka.hostname
if kafka.port:
    kafka_host = f"{kafka_host}:{kafka.port}"
KafkaManagerConfig(host=kafka_host, username=kafka.username, password=kafka.password)

# Кафка сервиса правил нотификации NR_service
KAFKA_URI_MODEL_SIGNAL = os.environ.get(
    "KAFKA_URI_MODEL_SIGNAL", "kafka://none:none@localhost:9092?topic=madirect.nr_service"
)
kafka_nr_service, kafka_nr_service_options = parse_uri_data(KAFKA_URI_MODEL_SIGNAL)
KAFKA_HOST_NR = f"{kafka_nr_service.hostname}:{kafka_nr_service.port}"
KAFKA_USERNAME_NR, KAFKA_PASSWORD_NR = kafka_nr_service.username, kafka_nr_service.password
KAFKA_TOPIC_NR = kafka_nr_service_options.pop("topic")

# Кафка сервиса броадкаста broadcast_service
KAFKA_URI_BROADCAST = os.environ.get(
    "KAFKA_URI_BROADCAST", "kafka://none:none@localhost:9092?topic=madirect.broadcast"
)
kafka_broadcast_service, kafka_broadcast_service_options = parse_uri_data(KAFKA_URI_BROADCAST)
KAFKA_HOST_BROADCAST = f"{kafka_broadcast_service.hostname}:{kafka_broadcast_service.port}"
KAFKA_USERNAME_BROADCAST, KAFKA_PASSWORD_BROADCAST = (
    kafka_broadcast_service.username,
    kafka_broadcast_service.password,
)
KAFKA_TOPIC_BROADCAST = kafka_broadcast_service_options.pop("topic")

ANALYTIC_KAFKA_URI_MODEL_SIGNAL = os.environ.get(
    "ANALYTIC_KAFKA_URI_MODEL_SIGNAL", "kafka://none:none@localhost:9092?topic=madirect.analytic"
)
kafka_analytic_service, kafka_analytic_service_options = parse_uri_data(ANALYTIC_KAFKA_URI_MODEL_SIGNAL)
KAFKA_HOST_ANALYTIC = f"{kafka_analytic_service.hostname}:{kafka_analytic_service.port}"
KAFKA_USERNAME_ANALYTIC, KAFKA_PASSWORD_ANALYTIC = (
    kafka_analytic_service.username,
    kafka_analytic_service.password,
)
KAFKA_TOPIC_ANALYTIC = kafka_analytic_service_options.pop("topic")

KAFKA_URI_DATACOURIER = os.environ.get(
    "KAFKA_URI_DATACOURIER",
    "kafka://none:none@localhost:9092?topic_in=madirect.datacourier.recepient.in&topic_out=madirect.datacourier.recepient.out",
)
kafka_datacourier_service, kafka_datacourer_service_options = parse_uri_data(KAFKA_URI_DATACOURIER)
KAFKA_HOST_DATACOURIER = f"{kafka_datacourier_service.hostname}:{kafka_datacourier_service.port}"
KAFKA_USERNAME_DATACOURIER, KAFKA_PASSWORD_DATACOURIER = (
    kafka_datacourier_service.username,
    kafka_datacourier_service.password,
)
KAFKA_TOPIK_DATACOURIER_OUT = kafka_datacourer_service_options.pop("topic_out")
KAFKA_TOPIK_DATACOURIER_IN = kafka_datacourer_service_options.pop("topic_in")

if DEBUG:
    INTERNAL_IPS = ["127.0.0.1"]
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

DATA_UPLOAD_MAX_MEMORY_SIZE = 1048576 * 100  # bytes * MB

if IS_LOCAL_SERVER:
    SERVER_IP = "127.0.0.1"
else:
    SERVER_IP = socket.gethostbyname(SERVICE_DOMAIN)  # оно может ломаться при отсутсвии интернета, это норма

DNS_MADE_EASY_LINK = os.environ.get(
    "DNS_MADE_EASY", "http://127.0.0.1:8002?DNSMADEEASY_API_KEY=&DNSMADEEASY_SECRET_KEY="
)
DNSMadeEasyLink = ParseLink(DNS_MADE_EASY_LINK)
DNSMADEEASY_URL = DNSMadeEasyLink.url_path
DNSMADEEASY_API_KEY = DNSMadeEasyLink.options.get("API_KEY", "")
DNSMADEEASY_SECRET_KEY = DNSMadeEasyLink.options.get("SECRET_KEY", "").encode("utf-8")

WHAT_IS_MA_URL = os.environ.get("WHAT_IS_MA_URL", "https://ma.direct/executors/whatis-madirect")

DATETIME_INPUT_FORMATS += ("%Y-%m-%dT%H:%M:%S.%fZ",)

AUTHSERV_LINK = os.environ.get("AUTHSERV", "")
AuthServLink = ParseLink(AUTHSERV_LINK)
AUTHSERV_HOST = AuthServLink.url_path
AUTHSERV_TOKEN = AuthServLink.options.get("AUTH_TOKEN", "")
AUTHSERV_SERVICE_NAME = AuthServLink.options.get("SERVICE_NAME")

IMPORT_EXPORT_USE_TRANSACTIONS = True

CONFLUENCE_WIKI_TOKEN = os.environ.get("CONFLUENCE_WIKI_TOKEN", "")

SERVICE_HOST = os.environ.get("SERVICE_HOST", "http://127.0.0.1:8000")

MA_API_SERVICE_LINK = os.environ.get("MA_API_SERVICE", "http://127.0.0.1:8003?AUTH_TOKEN=123qweasd")
MaApiService_LINK = ParseLink(MA_API_SERVICE_LINK)
MA_API_SERVICE_HOST = MaApiService_LINK.url_path
MA_API_SERVICE_AUTH_TOKEN = MaApiService_LINK.options.get("AUTH_TOKEN", "123qweasd")
MA_API_SERVICE_AUTH_HEADER = f"TRUST {MA_API_SERVICE_AUTH_TOKEN}"

NR_SERVICE_LINK = os.environ.get("NR_SERVICE", "http://127.0.0.1:8005?AUTH_TOKEN=123qweasd")
NRService_LINK = ParseLink(NR_SERVICE_LINK)
NR_SERVICE_HOST = NRService_LINK.url_path
NR_SERVICE_AUTH_TOKEN = NRService_LINK.options.get("AUTH_TOKEN", "")
NOTIFICATION_RULES_URL = urljoin(NR_SERVICE_HOST, "/api/v1/notification-rules/")

# BACKGROUND SERVICE GRPC

BACKGROUND_GRPC_HOST = os.environ.get("BACKGROUND_GRPC_HOST")
BACKGROUND_GRPC_PORT = os.environ.get("BACKGROUND_GRPC_PORT")
GRPC_MICROSERVICE_ON = os.environ.get("GRPC_MICROSERVICE_ON", False)

TREASURY_HOST = os.environ.get("TREASURY_HOST")
TREASURY_TOKEN = os.environ.get("TREASURY_TOKEN")

BILLING_TYPE = os.environ.get("BILLING_TYPE", "old")

REALM_WORKS_ID = os.environ.get("REALM_WORKS_ID", 1)


CELERY_BEAT_SCHEDULE = {
    "delete_bad_reservation_from_broadcast": {
        "task": "tasks.tasks.delete_bad_reservation_from_broadcast",
        "schedule": timedelta(minutes=5),
        "options": {"queue": CELERY_QUEUE},
    },
}
