
from flask_restful import reqparse

from controllers.app_api import AppApiResource, api
from models.model import App
from mylogger import logger
from services.role_model_customize_service import post_knowledge_level

"""
modelStudentId	模范生编码	String	
knowledgeDomain	模范生知识领域	String	
KnowledgeLevel	模范生知识层次	float	
"""


class KnowledgeLevelApi(AppApiResource):
    def post(self, app_model: App):
        """
        knowledge_level api
        ---
        tags:
          - knowledge_level
        parameters:
            - in: body
              name: body
              schema:
                id: knowledge_level
                required:
                  - modelStudentId
                properties:
                  modelStudentId:
                    type: string
                    description: modelStudentId
                  knowledgeDomain:
                    type: string
                    description: knowledgeDomain
                  KnowledgeLevel:
                    type: float
                    description: KnowledgeLevel
        responses:
            200:
                description: knowledge_level
                schema:
                id: knowledge_level
                properties:
                    result:
                    type: string
                    default: success
        """
        parser = reqparse.RequestParser()
        parser.add_argument('modelStudentId', type=str, required=True, help='modelStudentId')
        parser.add_argument('knowledgeDomain', type=str, required=True, help='knowledgeDomain')
        parser.add_argument('KnowledgeLevel', type=float, required=True, help='KnowledgeLevel')
        args = parser.parse_args()
        modelStudentId = args['modelStudentId']
        knowledgeDomain = args['knowledgeDomain']
        KnowledgeLevel = args['KnowledgeLevel']
        result = post_knowledge_level(modelStudentId, knowledgeDomain, KnowledgeLevel)
        logger.info(f"result: {result}")
        return {'result': 'success'}

    # def patch(self, app_model: App):
    #     """
    #     knowledge_level api
    #     ---
    #     tags:
    #       - knowledge_level
    #     parameters:
    #         - in: body
    #             name: body
    #             schema:
    #             id: knowledge_level
    #             required:
    #                 - modelStudentId
    #             properties:
    #                 modelStudentId:
    #                 type: string
    #                 description: modelStudentId
    #                 knowledgeDomain:
    #                 type: string
    #                 description: knowledgeDomain
    #                 KnowledgeLevel:
    #                 type: float
    #                 description: KnowledgeLevel
    #     responses:
    #         200:
    #             description: knowledge_level
    #             schema:
    #             id: knowledge_level
    #             properties:
    #                 result:
    #                 type: string
    #                 default: success
    #     """
    #     parser = reqparse.RequestParser()
    #     parser.add_argument('modelStudentId', type=str, required=True, help='modelStudentId')
    #     parser.add_argument('knowledgeDomain', type=str, required=True, help='knowledgeDomain')
    #     parser.add_argument('KnowledgeLevel', type=float, required=True, help='KnowledgeLevel')
    #     args = parser.parse_args()
    #     modelStudentId = args['modelStudentId']
    #     knowledgeDomain = args['knowledgeDomain']
    #     KnowledgeLevel = args['KnowledgeLevel']
    #     result = post_knowledge_level(modelStudentId, knowledgeDomain, KnowledgeLevel)
    #     logger.info(f"result: {result}")
    #     return {'result': 'success'}


api.add_resource(KnowledgeLevelApi, '/knowledge_level')
