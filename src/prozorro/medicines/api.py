from aiohttp import web
from aiohttp_swagger import setup_swagger
from prozorro import version
from prozorro.medicines.middleware import request_id_middleware, request_unpack_params
from prozorro.medicines.db import init_mongodb, cleanup_db_client
from prozorro.medicines.logging import AccessLogger, setup_logging
from prozorro.medicines.handlers import (
    get_version,
    ping_handler,
    get_registry,
)
from prozorro.medicines.settings import SENTRY_DSN, SWAGGER_DOC_AVAILABLE
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
import sentry_sdk
import logging

logger = logging.getLogger(__name__)


def create_application():
    app = web.Application(
        middlewares=(
            request_id_middleware,
            request_unpack_params,
        ),
        client_max_size=1024 ** 2 * 100
    )
    app.router.add_get("/api/1.0/ping", ping_handler)
    app.router.add_get("/api/1.0/registry/{name}.json", get_registry)
    app.router.add_get("/api/1.0/version", get_version, allow_head=False)

    app.on_startup.append(init_mongodb)
    app.on_cleanup.append(cleanup_db_client)
    return app


if __name__ == "__main__":
    setup_logging()
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[AioHttpIntegration()]
        )
    logger.info("Starting app on 0.0.0.0:80")

    application = create_application()

    if SWAGGER_DOC_AVAILABLE:
        setup_swagger(
            application,
            title='RMS API',
            description='RMS API description',
            api_version=version,
            ui_version=3,
        )
    web.run_app(
        application,
        host="0.0.0.0",
        port=80,
        access_log_class=AccessLogger,
        print=None
    )
