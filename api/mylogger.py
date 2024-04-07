# import logging
# import colorlog
import json
import os
import traceback
import uuid

import flask
from loguru import logger


def get_request_id():
    if getattr(flask.g, 'request_id', None):
        return flask.g.request_id

    new_uuid = uuid.uuid4().hex[:10]
    flask.g.request_id = new_uuid

    return new_uuid


def add_req_id(record):
    record['req_id'] = get_request_id() if flask.has_request_context() else '          '
    # record['req_id'] = get_request_id()
    return True


def serialize(record):
    subset = {
        "time": record["time"].__format__('YYYY-MM-DD HH:mm:ss.SSS'),
        "level": record["level"].name,
        "message": record["message"],
        "req_id": get_request_id() if flask.has_request_context() else '          '
    }
    if record.get('exception'):
        subset["exception"] = '{}: {}, TraceBack: {}'.format(type(record["exception"].value).__name__,
                                                             record["exception"].value, traceback.format_stack())
    return json.dumps(subset, ensure_ascii=False)


def patching(record):
    record["extra"]["serialized"] = serialize(record)


logger = logger.patch(patching)

logger.add(
    "./log/log_{time:YYYY-MM-DD}.tsv",
    rotation="10000KB",
    serialize=False,
    encoding="utf-8",
    # format="{extra[serialized]}"
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | {req_id} | <level>{level: <8}</level> | <cyan>{"
           "name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    filter=add_req_id,
)

from cmreslogging.handlers import CMRESHandler

if os.environ.get("MODE", "api") == "api":
    es_handler = CMRESHandler(hosts=[{'host': os.environ.get("ES_HOST", "127.0.0.1"), 'port': 9200}],
                              # 可以配置对应的认证权限
                              auth_type=CMRESHandler.AuthType.NO_AUTH,
                              es_index_name='log',  # 不需要提前创建Index
                              # 一个月分一个 Index,默认为按照每天分Index,示例:test-2020.12.02
                              index_name_frequency=CMRESHandler.IndexNameFrequency.MONTHLY,
                              # 额外增加环境标识
                              es_additional_fields={'environment': os.environ.get("ENV", "dev")}
                              )
    logger.add(es_handler)

# logger.add(
#     sys.stdout,
#     level="INFO",
#     format="{extra[serialized]}"
# )

# def get_logger():
#     logger = logging.getLogger(__name__)
#     # 去除原本handler
#     logger.handlers = []
#     # Create a handler
#     handler = logging.StreamHandler()
#
#     log_colors_config = {
#         'DEBUG': 'white',  # cyan white
#         'INFO': 'green',
#         'WARNING': 'yellow',
#         'ERROR': 'red',
#         'CRITICAL': 'bold_red',
#     }
#
#     # Define a formatter
#     console_formatter = colorlog.ColoredFormatter(
#         fmt='%(log_color)s[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s',
#         datefmt='%Y-%m-%d  %H:%M:%S',
#         log_colors=log_colors_config
#     )
#
#     # Associate the formatter with the handler
#     handler.setFormatter(console_formatter)
#
#     # Add the handler to the logger
#     if not logger.handlers:
#         logger.addHandler(handler)
#     logger.handler = []
#     handler.close()
#     return logger
#
# logger = get_logger()
