import logging
import colorlog
from loguru import logger
logger.add(
    "./log/log_{time:YYYY-MM-DD}.tsv",
    rotation="10000KB",
    serialize=False,
    encoding="utf-8",
)


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
