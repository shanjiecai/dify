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


class CountdownTask:

    def __init__(self):
        self._running = True  # 定义线程状态变量

    def terminate(self):
        self._running = False

    def run(self, n):
        # run方法的主循环条件加入对状态变量的判断
        while self._running and n > 0:
            print('T-minus', n)
            n -= 1
            time.sleep(5)
        print("thread is ended")

    def real_time_update(self, dataset_upload_real_time, app_context: AppContext):
        with app_context:
            while self._running:
                try:
                    # 获取当前日期
                    current_date = datetime.datetime.utcnow()
                    update_dataset_id_with_conversation_id_pipeline(
                        conversation_id=dataset_upload_real_time.conversation_id,
                        group_id=dataset_upload_real_time.group_id,
                        dataset_id=dataset_upload_real_time.dataset_id)
                except:
                    logger.info(f"{traceback.format_exc()}")
                time.sleep(60 * 60 * 8)


task_list = []


def init_dataset_update_real_time(main_app: Flask):
    env = main_app.config.get('ENV')
    mode = main_app.config.get('MODE')
    logger.info(f"init_dataset_update_real_time, 当前环境：{env}, 当前模式：{mode}")
    with main_app.app_context():
        try:
            if env == 'production' and mode == 'api':
                # if mode == 'api':
                dataset_upload_real_time_list = DatasetUpdateRealTimeService.get_all_dataset_upload_real_time()
            else:
                dataset_upload_real_time_list = []
        except:
            logger.info(f"{traceback.format_exc(limit=10)}")
            dataset_upload_real_time_list = []
    logger.info(f"dataset_upload_real_time_list: {dataset_upload_real_time_list}")
    if dataset_upload_real_time_list:
        for dataset_upload_real_time in dataset_upload_real_time_list:
            task = CountdownTask()
            t = threading.Thread(target=task.real_time_update, args=(dataset_upload_real_time, main_app.app_context()))
            t.start()
            # 便于之后关闭线程
            task_list.append(task)


def restart_dataset_update_real_time(main_app: Flask):
    for task in task_list:
        task.terminate()
    task_list.clear()
    env = main_app.config.get('ENV')
    mode = main_app.config.get('MODE')
    logger.info(f"restart_dataset_update_real_time, 当前环境：{env}, 当前模式：{mode}")
    with main_app.app_context():
        try:
            if env == 'production' and mode == 'api':
                # if mode == 'api':
                dataset_upload_real_time_list = DatasetUpdateRealTimeService.get_all_dataset_upload_real_time()
            else:
                dataset_upload_real_time_list = []
        except:
            logger.info(f"{traceback.format_exc(limit=10)}")
            dataset_upload_real_time_list = []
    logger.info(f"restart dataset_upload_real_time_list: {dataset_upload_real_time_list}")
    if dataset_upload_real_time_list:
        for dataset_upload_real_time in dataset_upload_real_time_list:
            task = CountdownTask()
            t = threading.Thread(target=task.real_time_update, args=(dataset_upload_real_time, main_app.app_context()))
            t.start()
            # 便于之后关闭线程
            task_list.append(task)
