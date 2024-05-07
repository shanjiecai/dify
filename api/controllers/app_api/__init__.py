from flask import Blueprint

from libs.external_api import ExternalApi

bp = Blueprint('app_api', __name__, url_prefix='/backend-api/v1')
api = ExternalApi(bp)

from .app import app, completion, conversation, message
from .copywriter import *
from .img import *
from .quote import *
from .role_model_customize import knowledge_level, persona_matrix
from .summarize import *
