from flask_restful import reqparse

from controllers.app_api import AppApiResource, api
from models.model import App
from services.role_model_customize_service import (
    get_role_model_customize_list,
    post_persona_matrix,
)

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
        parser.add_argument("modelStudentId", type=str, required=True)
        parser.add_argument("portraitDesign", type=list, required=True, action="append")
        args = parser.parse_args()
        model_student_id = args.get("modelStudentId")
        portrait_design = args.get("portraitDesign")
        result = post_persona_matrix(model_student_id, portrait_design)
        return {"result": "success", "personaMatrix": result}


"""
curl -X GET -H "Content-Type: application/json" -d '{"category":"RoleModel","page": 1,"pageSize":10}' http://172.31.18.163:8000/RoleModel/v1   参数  category： 类型   page： 页数（页数从1开始）pageSize：数量
"""


class RoleModelCustomizelist(AppApiResource):
    def get(self):
        """
        role_model_customize_list api
        ---
        tags:
          - role_model_customize_list
        # parameters:
        #     - in: body
        #       name: body
        #       required: true
        #       schema:
        #         type: object
        #         id: role_model_customize_list
        #         properties:
        #           category:
        #             type: string
        #             description: category
        #           page:
        #             type: integer
        #             description: page
        #           pageSize:
        #             type: integer
        #             description: pageSize

        responses:
            200:
                description: role_model_customize_list
                schema:
                id: role_model_customize_list
                properties:
                    result:
                    type: string
                    default: success
                    roleModelList:
                    type: array
                    items:
                        type: object
                        properties:
                            modelStudentId:
                            type: string
                            人格:
                            type: string
                            价值观:
                            type: string
                            智能:
                            type: string
                            领导风格:
                            type: string
                            知识边界:
                            type: string
        """
        parser = reqparse.RequestParser()
        parser.add_argument("category", type=str, required=False, default="RoleModel")
        parser.add_argument("page", type=int, required=False, default=1)
        parser.add_argument("pageSize", type=int, required=False, default=20)
        args = parser.parse_args()
        category = args.get("category")
        page = args.get("page")
        page_size = args.get("pageSize")
        result = get_role_model_customize_list(category, page, page_size)
        return {"result": "success", "roleModelList": result}


api.add_resource(PersonaMatrixApi, "/role_model_customize/persona_matrix")
api.add_resource(RoleModelCustomizelist, "/role_model_customize/list")
