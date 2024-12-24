from libs import version_utils

# preparation before creating app
version_utils.check_supported_python_version()


def is_db_command():
    import sys

    if len(sys.argv) > 1 and sys.argv[0].endswith("flask") and sys.argv[1] == "db":
        return True
    return False


# create app
if is_db_command():
    from app_factory import create_migrations_app

    app = create_migrations_app()
else:
    from app_factory import create_app
    from libs import threadings_utils

    threadings_utils.apply_gevent_threading_patch()

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
