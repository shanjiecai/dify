import json
from typing import Optional, Union

from core.generator.llm_generator import LLMGenerator
from core.memory.token_buffer_memory import TokenBufferMemory
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from extensions.ext_database import db
from libs.infinite_scroll_pagination import InfiniteScrollPagination
from models.account import Account
from models.model import App, AppModelConfig, EndUser, Message, MessageFeedback
from models.dataset import DatasetUpdateRealTime
from services.conversation_service import ConversationService
from services.errors.app_model_config import AppModelConfigBrokenError
from services.errors.conversation import ConversationCompletedError, ConversationNotExistsError
from services.errors.message import (
    FirstMessageNotExistsError,
    LastMessageNotExistsError,
    MessageNotExistsError,
    SuggestedQuestionsAfterAnswerDisabledError,
)


class DatasetUpdateRealTimeService:
    @classmethod
    def get(cls, dataset_id: str, group_id: str = None, conversation_id: str = None) -> Optional[DatasetUpdateRealTime]:
        if not conversation_id and not group_id:
            return None

        dataset_update_real_time_item = db.session.query(DatasetUpdateRealTime).filter(
            DatasetUpdateRealTime.conversation_id == conversation_id,
            DatasetUpdateRealTime.group_id == group_id,
            DatasetUpdateRealTime.dataset_id == dataset_id).first()

        return dataset_update_real_time_item

    @classmethod
    def get_all_dataset_upload_real_time(cls, conversation_id: Optional[str] = None) -> list[DatasetUpdateRealTime]:
        # if not conversation_id:
        #     return []

        dataset_update_real_time_items = db.session.query(DatasetUpdateRealTime).filter(
            DatasetUpdateRealTime.conversation_id == conversation_id).all()

        return dataset_update_real_time_items
