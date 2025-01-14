import logging
import mimetypes
import os
from pathlib import Path
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.httpx import (
    HTTPXClientInstrumentor,
)
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from quart import Blueprint, Quart, send_from_directory
from quart_cors import cors
from utils.blueprintutils import get_blueprints

# Fix Windows registry issue with mimetypes
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

bp = Blueprint('route', __name__, static_folder="static")

@bp.route("/")
async def index():
    return await bp.send_static_file("index.html")

# Empty page is recommended for login redirect to work.
# See https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/initialization.md#redirecturi-considerations for more information
@bp.route("/redirect")
async def redirect():
    return ""


@bp.route("/favicon.ico")
async def favicon():
    return await bp.send_static_file("favicon.ico")


@bp.route("/assets/<path:path>")
async def assets(path):
    return await send_from_directory(Path(__file__).resolve().parent / "static" / "assets", path)

def create_app():
    app = Quart(__name__)

    blueprints = get_blueprints()

    # register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # register route
    app.register_blueprint(bp)

    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        app.logger.info("APPLICATIONINSIGHTS_CONNECTION_STRING is set, enabling Azure Monitor")
        configure_azure_monitor()
        # This tracks HTTP requests made by aiohttp:
        AioHttpClientInstrumentor().instrument()
        # This tracks HTTP requests made by httpx:
        HTTPXClientInstrumentor().instrument()
        # This tracks OpenAI SDK requests:
        OpenAIInstrumentor().instrument()
        # This middleware tracks app route requests:
        app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)  # type: ignore[assignment]

    # Log levels should be one of https://docs.python.org/3/library/logging.html#logging-levels
    # Set root level to WARNING to avoid seeing overly verbose logs from SDKS
    logging.basicConfig(level=logging.WARNING)
    # Set our own logger levels to INFO by default
    app_level = os.getenv("APP_LOG_LEVEL", "INFO")
    app.logger.setLevel(os.getenv("APP_LOG_LEVEL", app_level))
    logging.getLogger("scripts").setLevel(app_level)

    if allowed_origin := os.getenv("ALLOWED_ORIGIN"):
        app.logger.info("ALLOWED_ORIGIN is set, enabling CORS for %s", allowed_origin)
        cors(app, allow_origin=allowed_origin, allow_methods=["GET", "POST"])
    return app
