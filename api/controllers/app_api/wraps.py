
from flask import request
from flask_restful import Resource
from werkzeug.exceptions import Unauthorized

from extensions.ext_database import db
from models.model import App


def validate_app_token(func):
    def decorated_view(*args, **kwargs):
        auth_token = validate_and_get_api_token()
        if auth_token != "b10dd914-d28d-10b4-11c4-3a8b61d8a77f":
            raise Unauthorized('Invalid Authorization header')
        if request.path in ["/backend-api/v1/app/list", "/backend-api/v1/person/list"]:
            return func(*args, **kwargs)
        if request.method == "GET":
            app_id = request.args.get('app_id')
        else:
            app_id = request.json.get('app_id')
        app_model = db.session.query(App).filter(App.id == app_id).first()
        return func(app_model, *args, **kwargs)
    return decorated_view


def validate_and_get_api_token():
    auth_header = request.headers.get('Authorization')
    if auth_header is None or ' ' not in auth_header:
        raise Unauthorized("Authorization header must be provided and start with 'Bearer'")

    auth_scheme, auth_token = auth_header.split(None, 1)
    auth_scheme = auth_scheme.lower()

    if auth_scheme != 'bearer':
        raise Unauthorized("Authorization scheme must be 'Bearer'")

    return auth_token


class AppApiResource(Resource):
    method_decorators = [validate_app_token]

