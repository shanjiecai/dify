from flask import Blueprint

from libs.external_api import ExternalApi

bp = Blueprint('app_api', __name__, url_prefix='/backend-api/v1')
api = ExternalApi(bp)

from .app import app, completion, conversation, message
from .copywriter import *
from .summarize import *
