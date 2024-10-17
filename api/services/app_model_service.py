from typing import Optional, Union

# from core.completion import Completion
from extensions.ext_database import db
from models.account import Account
from models.model import App, AppModelConfig, Conversation, EndUser, Message
from services.errors.app_model_config import AppModelConfigBrokenError


class AppModelService:
    @classmethod
    def get_app_model_config_list(cls) -> list[App]:
        app_list = db.session.query(App).filter(App.name != "test").all()
        # 按照时间倒叙排序，如果有多个app_model_configs，取最新的一个
        app_list = sorted(app_list, key=lambda x: x.created_at, reverse=True)
        name_list = []
        # 获取app_model_configs下的model_id
        for app in app_list:
            if "test" in app.name:
                app_list.remove(app)
                continue
            # 去除重名
            if app.name in name_list:
                app_list.remove(app)
                continue
            try:
                app_model_config = cls.get_app_model_config(app)
                # print(f"{app.name} {app_model_config.model_id}")
                app.model_id = app_model_config.model_id
            except:
                app.model_id = None
            name_list.append(app.name)
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
    def get_app_model_by_app_id(cls, app_id: str) -> App:
        app_model = db.session.query(App).filter(App.id == app_id).first()
        if not app_model:
            raise AppModelConfigBrokenError()

        return app_model

    @classmethod
    def get_app_model_by_app_name(cls, app_name: str) -> App:
        app_model = db.session.query(App).filter(App.name == app_name).first()
        return app_model

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
