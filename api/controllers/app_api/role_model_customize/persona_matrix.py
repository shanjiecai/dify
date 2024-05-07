
from flask_restful import reqparse

from controllers.app_api import AppApiResource, api
from models.model import App
from services.role_model_customize_service import post_persona_matrix

"""
序号	参数名称	参数说明	类型	备注
1	modelStudentId	模范生编码	String	
2	portraitDesign	模范生人设画像标签	List	
"""


class PersonaMatrixApi(AppApiResource):
    def post(self, app_model: App):
        """
        persona_matrix api
        ---
        tags:
          - persona_matrix
        parameters:
            - in: body
              name: body
              required: true
              schema:
                type: object
                id: persona_matrix
                properties:
                  modelStudentId:
                    type: string
                    description: modelStudentId
                  portraitDesign:
                    type: array
                    items:
                      type: string
                    description: portraitDesign

        responses:
            200:
                description: persona_matrix
                schema:
                id: persona_matrix
                properties:
                    result:
                    type: string
                    default: success
                    personaMatrix:
                    type: array
                    items:
                        type: string
        """
        parser = reqparse.RequestParser()
        parser.add_argument('modelStudentId', type=str, required=True)
        parser.add_argument('portraitDesign', type=list, required=True, action='append')
        args = parser.parse_args()
        model_student_id = args.get('modelStudentId')
        portrait_design = args.get('portraitDesign')
        result = post_persona_matrix(model_student_id, portrait_design)
        return {'result': 'success', 'personaMatrix': result}


api.add_resource(PersonaMatrixApi, '/persona_matrix')
