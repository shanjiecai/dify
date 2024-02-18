from typing import Optional

from extensions.ext_database import db
from models.dataset import DatasetUpdateRealTime


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
