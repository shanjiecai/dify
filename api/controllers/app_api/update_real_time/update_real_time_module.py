import datetime
import threading
import time
import traceback

from flask import Flask
from flask.ctx import AppContext

from controllers.app_api.app.utils import *
from controllers.app_api.update_real_time import update_dataset_id_with_conversation_id_pipeline

# from core.completion import Completion
from mylogger import logger
from services.dataset_update_real_time_service import DatasetUpdateRealTimeService


def real_time_update(dataset_upload_real_time, app_context: AppContext):
    with app_context:
        while True:
            try:
                # 获取当前日期
                current_date = datetime.datetime.utcnow()
                update_dataset_id_with_conversation_id_pipeline(conversation_id=dataset_upload_real_time.conversation_id,
                                                                group_id=dataset_upload_real_time.group_id,
                                                                dataset_id=dataset_upload_real_time.dataset_id)
            except:
                logger.info(f"{traceback.format_exc()}")
            time.sleep(60 * 60 * 8)


def init_dataset_update_real_time(main_app: Flask):
    env = main_app.config.get('ENV')
    mode = main_app.config.get('MODE')
    logger.info(f"init_dataset_update_real_time, 当前环境：{env}, 当前模式：{mode}")
    with main_app.app_context():
        try:
            # if env == 'production' and mode == 'api':
                dataset_upload_real_time_list = DatasetUpdateRealTimeService.get_all_dataset_upload_real_time()
            # else:
            #     dataset_upload_real_time_list = []
        except:
            logger.info(f"{traceback.format_exc(limit=10)}")
            dataset_upload_real_time_list = []
    logger.info(f"dataset_upload_real_time_list: {dataset_upload_real_time_list}")
    if dataset_upload_real_time_list:
        for dataset_upload_real_time in dataset_upload_real_time_list:
            t = threading.Thread(target=real_time_update, args=(dataset_upload_real_time, main_app.app_context()))
            t.start()
