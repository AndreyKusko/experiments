import os
from django.apps import apps
from django.conf import settings
from django.core.wsgi import get_wsgi_application
import asyncio


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
apps.populate(settings.INSTALLED_APPS)

from clients.afka_consumer import consumer
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from starlette.middleware.cors import CORSMiddleware

from api.views import router


def get_application() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.mount("/django", WSGIMiddleware(get_wsgi_application()))

    asyncio.ensure_future(consumer.start())
    # clickhouse_client.command('CREATE TABLE IF NOT EXISTS project_instance (key UInt32, value String, metric Float64) ENGINE MergeTree ORDER BY key')
    return app


app = get_application()
