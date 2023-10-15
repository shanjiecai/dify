import json
from typing import Optional, Union, List

from core.completion import Completion
from core.generator.llm_generator import LLMGenerator
from libs.infinite_scroll_pagination import InfiniteScrollPagination
from extensions.ext_database import db
from models.account import Account
from models.model import App, EndUser, Message, MessageFeedback, AppModelConfig, Conversation
from services.conversation_service import ConversationService
from services.errors.app_model_config import AppModelConfigBrokenError
from services.errors.conversation import ConversationNotExistsError, ConversationCompletedError
from services.errors.message import FirstMessageNotExistsError, MessageNotExistsError, LastMessageNotExistsError, \
    SuggestedQuestionsAfterAnswerDisabledError


class AppModelService:
    @classmethod
    def get_app_model_config_list(cls) -> List[App]:
        app_list = db.session.query(App).all()
        # 获取app_model_configs下的model_id
        for app in app_list:
            app_model_config = cls.get_app_model_config(app)
            app.model_id = app_model_config.model_id
        return app_list

    @classmethod
    def get_app_model_config(cls, app_model: App) -> AppModelConfig:
        app_model_config = db.session.query(AppModelConfig).filter(AppModelConfig.app_id == app_model.id).first()
        if not app_model_config:
            raise AppModelConfigBrokenError()

        return app_model_config

    @classmethod
    def get_app_model_config_by_tenant_id(cls, tenant_id: str) -> AppModelConfig:
        app_model = db.session.query(App).filter(App.tenant_id == tenant_id).first()
        if not app_model:
            raise AppModelConfigBrokenError()

        return cls.get_app_model_config(app_model)

    @classmethod
    def get_app_model_config_by_app_id(cls, app_id: str) -> AppModelConfig:
        app_model = db.session.query(App).filter(App.id == app_id).first()
        if not app_model:
            raise AppModelConfigBrokenError()

        return cls.get_app_model_config(app_model)

    @classmethod
    def get_app_model_config_by_app_model_id(cls, app_model_id: str) -> AppModelConfig:
        app_model = db.session.query(App).filter(App.id == app_model_id).first()
        if not app_model:
            raise AppModelConfigBrokenError()

        return cls.get_app_model_config(app_model)

    @classmethod
    def get_app_model_config_by_app_model(cls, app_model: App) -> AppModelConfig:
        return cls.get_app_model_config(app_model)

    @classmethod
    def get_app_model_config_by_user(cls, user: Optional[Union[Account | EndUser]]) -> AppModelConfig:
        if not user:
            raise AppModelConfigBrokenError()

        app_model = db.session.query(App).filter(App.id == user.app_id).first()
        if not app_model:
            raise AppModelConfigBrokenError()

        return cls.get_app_model_config(app_model)

    @classmethod
    def get_app_model_config_by_conversation(cls, conversation: Conversation) -> AppModelConfig:
        app_model = db.session.query(App).filter(App.id == conversation.app_id).first()
        if not app_model:
            raise AppModelConfigBrokenError()

        return cls.get_app_model_config(app_model)

    @classmethod
    def get_app_model_config_by_message(cls, message: Message) -> AppModelConfig:
        app_model = db.session.query(App).filter(App.id == message.app_id).first()
        if not app_model:
            raise AppModelConfigBrokenError()

        return cls.get_app_model_config(app_model)