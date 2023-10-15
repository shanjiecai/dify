# -*- coding:utf-8 -*-
from flask_restful import fields, marshal_with, reqparse
from flask_restful.inputs import int_range

from controllers.app_api import api
from controllers.app_api.wraps import AppApiResource

from models.model import App
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


api.add_resource(AppListApi, '/app/list')
