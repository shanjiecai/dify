import json
import logging
from datetime import datetime, timezone
from typing import cast

from flask_login import current_user
from flask_sqlalchemy.pagination import Pagination

from configs import dify_config
from constants.model_template import default_app_templates
from core.agent.entities import AgentToolEntity
from core.app.features.rate_limiting import RateLimit
from core.errors.error import LLMBadRequestError, ProviderTokenNotInitError
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelPropertyKey, ModelType
from core.model_runtime.model_providers.__base.large_language_model import LargeLanguageModel
from core.tools.tool_manager import ToolManager
from core.tools.utils.configuration import ToolParameterConfigurationManager
from events.app_event import app_was_created
from extensions.ext_database import db
from models.account import Account
from models.model import App, AppMode, AppModelConfig, ApiToken
from models.tools import ApiToolProvider
from services.tag_service import TagService
from tasks.remove_app_and_related_data_task import remove_app_and_related_data_task


class APITokensService:
    @classmethod
    def get_api_tokens_from_app_name(cls, app_name: str) -> ApiToken:
        app = db.session.query(App).filter_by(name=app_name).first()
        ApiToken = db.session.query(ApiToken).filter_by(
            app_id=app.id,
            type="app"
        ).first()
        return ApiToken
