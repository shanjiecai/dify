from typing import Optional

from extensions.ext_database import db
from models.dataset import DatasetUpdateRealTimeSocialAgent


class DatasetUpdateRealTimeSocialAgentService:
    # @classmethod
    # def get(cls, dataset_id: str, group_id: str = None, conversation_id: str = None) -> Optional[DatasetUpdateRealTimeSocialAgent]:
    #     if not conversation_id and not group_id:
    #         return None
    #
    #     dataset_update_real_time_item = db.session.query(DatasetUpdateRealTimeSocialAgent).filter(
    #         DatasetUpdateRealTime.conversation_id == conversation_id,
    #         DatasetUpdateRealTime.group_id == group_id,
    #         DatasetUpdateRealTime.dataset_id == dataset_id).first()
    #
    #     return dataset_update_real_time_item

    @classmethod
    def get_all_dataset_upload_real_time_social_agent(cls, app_id: Optional[str] = None) -> list[DatasetUpdateRealTimeSocialAgent]:

        if not app_id:
            dataset_update_real_time_social_agent_items = db.session.query(DatasetUpdateRealTimeSocialAgent).all()
        else:
            dataset_update_real_time_social_agent_items = db.session.query(DatasetUpdateRealTimeSocialAgent).filter(
                DatasetUpdateRealTimeSocialAgent.app_id == app_id).all()

        return dataset_update_real_time_social_agent_items
