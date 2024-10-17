from typing import Optional

from extensions.ext_database import db
from models.dataset import DatasetUpdateRealTimeSocialAgent


class DatasetUpdateRealTimeSocialAgentService:

    @classmethod
    def get_all_dataset_upload_real_time_social_agent(
        cls, app_id: Optional[str] = None
    ) -> list[DatasetUpdateRealTimeSocialAgent]:

        if not app_id:
            dataset_update_real_time_social_agent_items = db.session.query(DatasetUpdateRealTimeSocialAgent).all()
        else:
            dataset_update_real_time_social_agent_items = (
                db.session.query(DatasetUpdateRealTimeSocialAgent)
                .filter(DatasetUpdateRealTimeSocialAgent.app_id == app_id)
                .all()
            )

        return dataset_update_real_time_social_agent_items
