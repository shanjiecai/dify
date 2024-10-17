import os
import sys
from logging.handlers import RotatingFileHandler

if os.environ.get("DEBUG", "false").lower() != "true":
    from gevent import monkey

    monkey.patch_all()

    import grpc.experimental.gevent

    grpc.experimental.gevent.init_gevent()

import json
import logging
import threading
import time
import warnings

from flask import Flask, Response, request
from flask_cors import CORS
from werkzeug.exceptions import Unauthorized

# from core.model_providers.providers import hosted
import contexts
from commands import register_commands
from configs import dify_config

# DO NOT REMOVE BELOW
from events import event_handlers  # noqa: F401
from extensions import (
    ext_celery,
    ext_code_based_extension,
    ext_compress,
    ext_database,
    ext_hosting_provider,
    ext_login,
    ext_mail,
    ext_migrate,
    ext_proxy_fix,
    ext_redis,
    ext_sentry,
    ext_storage,
)
from extensions.ext_database import db
from extensions.ext_login import login_manager
from libs.passport import PassportService

# TODO: Find a way to avoid importing models here
from models import account, dataset, model, source, task, tool, tools, web  # noqa: F401
from services.account_service import AccountService

# DO NOT REMOVE ABOVE


warnings.simplefilter("ignore", ResourceWarning)

os.environ["TZ"] = "UTC"
# windows platform not support tzset
if hasattr(time, "tzset"):
    time.tzset()


class DifyApp(Flask):
    pass


# -------------
# Configuration
# -------------


config_type = os.getenv("EDITION", default="SELF_HOSTED")  # ce edition first


# ----------------------------
# Application Factory Function
# ----------------------------


def create_flask_app_with_configs() -> Flask:
    """
    create a raw flask app
    with configs loaded from .env file
    """
    dify_app = DifyApp(__name__)
    dify_app.config.from_mapping(dify_config.model_dump())

    # populate configs into system environment variables
    for key, value in dify_app.config.items():
        if isinstance(value, str):
            os.environ[key] = value
        elif isinstance(value, int | float | bool):
            os.environ[key] = str(value)
        elif value is None:
            os.environ[key] = ""

    return dify_app


def create_app() -> Flask:
    app = create_flask_app_with_configs()

    app.secret_key = app.config["SECRET_KEY"]

    log_handlers = None
    log_file = app.config.get("LOG_FILE")
    if log_file:
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        log_handlers = [
            RotatingFileHandler(
                filename=log_file,
                maxBytes=1024 * 1024 * 1024,
                backupCount=5,
            ),
            logging.StreamHandler(sys.stdout),
        ]

    logging.basicConfig(
        level=app.config.get("LOG_LEVEL"),
        format=app.config.get("LOG_FORMAT"),
        datefmt=app.config.get("LOG_DATEFORMAT"),
        handlers=log_handlers,
        force=True,
    )
    log_tz = app.config.get("LOG_TZ")
    if log_tz:
        from datetime import datetime

        import pytz

        timezone = pytz.timezone(log_tz)

        def time_converter(seconds):
            return datetime.utcfromtimestamp(seconds).astimezone(timezone).timetuple()

        for handler in logging.root.handlers:
            handler.formatter.converter = time_converter
    initialize_extensions(app)
    register_blueprints(app)
    register_commands(app)

    # hosted.init_app(app)

    # from controllers.app_api.app.active_module import init_active_chat
    # init_active_chat(app)

    # from controllers.app_api.update_real_time.update_real_time_module import init_dataset_update_real_time
    # init_dataset_update_real_time(app)

    from controllers.social_agent_api.update_real_time.update_real_time_module import (
        init_dataset_update_real_time_social_agent,
    )

    init_dataset_update_real_time_social_agent(app)

    # try:
    #     from elasticapm.contrib.flask import ElasticAPM
    #     app.config['ELASTIC_APM'] = {
    #         'SERVICE_NAME': 'monitor',
    #         'SECRET_TOKEN': '',
    #         'SERVER_URL': f'http://{os.environ.get("ES_HOST", "127.0.0.1")}:9200'
    #     }
    #     apm = ElasticAPM(app)
    # except:
    #     # print(traceback.format_exc())
    #     pass
    # import trace
    # trace.init_trace(app)
    return app


def initialize_extensions(app):
    # Since the application instance is now created, pass it to each Flask
    # extension instance to bind it to the Flask application instance (app)
    ext_compress.init_app(app)
    ext_code_based_extension.init()
    ext_database.init_app(app)
    ext_migrate.init(app, db)
    ext_redis.init_app(app)
    ext_storage.init_app(app)
    ext_celery.init_app(app)
    ext_login.init_app(app)
    ext_mail.init_app(app)
    ext_hosting_provider.init_app(app)
    ext_sentry.init_app(app)
    ext_proxy_fix.init_app(app)


# Flask-Login configuration
@login_manager.request_loader
def load_user_from_request(request_from_flask_login):
    """Load user based on the request."""
    if request.blueprint not in {"console", "inner_api"}:
        return None
    # Check if the user_id contains a dot, indicating the old format
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        auth_token = request.args.get("_token")
        if not auth_token:
            raise Unauthorized("Invalid Authorization token.")
    else:
        if " " not in auth_header:
            raise Unauthorized("Invalid Authorization header format. Expected 'Bearer <api-key>' format.")
        auth_scheme, auth_token = auth_header.split(None, 1)
        auth_scheme = auth_scheme.lower()
        if auth_scheme != "bearer":
            raise Unauthorized("Invalid Authorization header format. Expected 'Bearer <api-key>' format.")

    decoded = PassportService().verify(auth_token)
    user_id = decoded.get("user_id")

    logged_in_account = AccountService.load_logged_in_account(account_id=user_id)
    if logged_in_account:
        contexts.tenant_id.set(logged_in_account.current_tenant_id)
    return logged_in_account


@login_manager.unauthorized_handler
def unauthorized_handler():
    """Handle unauthorized requests."""
    return Response(
        json.dumps({"code": "unauthorized", "message": "Unauthorized."}),
        status=401,
        content_type="application/json",
    )


# register blueprint routers
def register_blueprints(app):
    from controllers.console import bp as console_app_bp
    from controllers.files import bp as files_bp
    from controllers.inner_api import bp as inner_api_bp
    from controllers.service_api import bp as service_api_bp
    from controllers.social_agent_api import bp as social_agent_api_bp
    from controllers.web import bp as web_bp

    CORS(
        social_agent_api_bp,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
        supports_credentials=True,
        resources={r"/*": {"origins": app.config["APP_API_CORS_ALLOW_ORIGINS"]}},
        expose_headers=["X-Version", "X-Env"],
    )
    app.register_blueprint(social_agent_api_bp)

    CORS(
        service_api_bp,
        allow_headers=["Content-Type", "Authorization", "X-App-Code"],
        methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    )
    app.register_blueprint(service_api_bp)

    CORS(
        web_bp,
        resources={r"/*": {"origins": app.config["WEB_API_CORS_ALLOW_ORIGINS"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-App-Code"],
        methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
        expose_headers=["X-Version", "X-Env"],
    )

    app.register_blueprint(web_bp)

    CORS(
        console_app_bp,
        resources={r"/*": {"origins": app.config["CONSOLE_CORS_ALLOW_ORIGINS"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
        expose_headers=["X-Version", "X-Env"],
    )

    app.register_blueprint(console_app_bp)

    # CORS(app_api_bp,
    #      resources={
    #          r"/*": {"origins": app.config['APP_API_CORS_ALLOW_ORIGINS']}},
    #      supports_credentials=True,
    #      allow_headers=['Content-Type', 'Authorization'],
    #      methods=['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'PATCH'],
    #      expose_headers=['X-Version', 'X-Env']
    #      )
    # app.register_blueprint(app_api_bp)

    CORS(files_bp, allow_headers=["Content-Type"], methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"])
    app.register_blueprint(files_bp)

    app.register_blueprint(inner_api_bp)

    # 列出所有的路由
    print(app.url_map)


# create app
app = create_app()
app.config["SWAGGER"] = {
    "title": "role model api",
}
from flasgger import Swagger

swag = Swagger(
    app,
    config={
        "specs_route": "/backend-api/docs",
        "specs": [
            {
                "endpoint": "/backend-api/apispec_1",
                "route": "/backend-api/apispec_1.json",
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/backend-api/flasgger_static",
    },
    merge=True,
)
celery = app.extensions["celery"]
config = app.config

if app.config.get("TESTING"):
    print("App is running in TESTING mode")


@app.after_request
def after_request(response):
    """Add Version headers to the response."""
    response.set_cookie("remember_token", "", expires=0)
    response.headers.add("X-Version", app.config["CURRENT_VERSION"])
    response.headers.add("X-Env", app.config["DEPLOY_ENV"])
    return response


@app.route("/health")
def health():
    return Response(
        json.dumps({"pid": os.getpid(), "status": "ok", "version": app.config["CURRENT_VERSION"]}),
        status=200,
        content_type="application/json",
    )


@app.route("/threads")
def threads():
    num_threads = threading.active_count()
    threads = threading.enumerate()

    thread_list = []
    for thread in threads:
        thread_name = thread.name
        thread_id = thread.ident
        is_alive = thread.is_alive()

        thread_list.append(
            {
                "name": thread_name,
                "id": thread_id,
                "is_alive": is_alive,
            }
        )

    return {
        "pid": os.getpid(),
        "thread_num": num_threads,
        "threads": thread_list,
    }


@app.route("/db-pool-stat")
def pool_stat():
    engine = db.engine
    return {
        "pid": os.getpid(),
        "pool_size": engine.pool.size(),
        "checked_in_connections": engine.pool.checkedin(),
        "checked_out_connections": engine.pool.checkedout(),
        "overflow_connections": engine.pool.overflow(),
        "connection_timeout": engine.pool.timeout(),
        "recycle_time": db.engine.pool._recycle,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
