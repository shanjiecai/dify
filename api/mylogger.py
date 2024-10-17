# import logging
# import colorlog
import json
import traceback
import uuid

import flask
from loguru import logger


def get_request_id():
    if getattr(flask.g, "request_id", None):
        return flask.g.request_id

    new_uuid = uuid.uuid4().hex[:10]
    flask.g.request_id = new_uuid

    return new_uuid


def add_req_id(record):
    record["req_id"] = get_request_id() if flask.has_request_context() else "          "
    # record['req_id'] = get_request_id()
    return True


def serialize(record):
    subset = {
        "time": record["time"].format("YYYY-MM-DD HH:mm:ss.SSS"),
        "level": record["level"].name,
        "message": record["message"],
        "req_id": get_request_id() if flask.has_request_context() else "          ",
    }
    if record.get("exception"):
        subset["exception"] = "{}: {}, TraceBack: {}".format(
            type(record["exception"].value).__name__, record["exception"].value, traceback.format_stack()
        )
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
