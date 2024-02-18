from flask_restful import fields, marshal_with, reqparse

from controllers.app_api import api
from controllers.app_api.wraps import AppApiResource
from services.app_model_service import AppModelService


class AppListApi(AppApiResource):
    """Resource for app variables."""

    parameters_fields = {
        'name': fields.String,
        'id': fields.String,
        'model': fields.String,
    }

    @marshal_with(parameters_fields)
    def get(self):
        """Retrieve app models list."""
        parser = reqparse.RequestParser()
        # parser.add_argument('page', type=int_range(1), default=1, location='args')
        # parser.add_argument('size', type=int_range(1, 100), default=10, location='args')
        # args = parser.parse_args()
        app_models = AppModelService.get_app_model_config_list()
        # 只取name和id
        app_models = [{'name': app_model.name, 'id': app_model.id, 'model': app_model.model_id} for app_model in app_models]
        return app_models


class PersonListApi(AppApiResource):
    person_name_fields = {
        'name': fields.String,
    }

    @marshal_with(person_name_fields)
    def get(self):
        # app_name去掉后面的()之后去重
        app_models = AppModelService.get_app_model_config_list()
        app_models = [app_model.name.split('(')[0] for app_model in app_models]
        app_models = list(set(app_models))
        return [{'name': app_model} for app_model in app_models]


api.add_resource(AppListApi, '/app/list')
api.add_resource(PersonListApi, '/person/list')
