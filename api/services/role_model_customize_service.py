import os

import requests

role_model_customize_service_url = os.getenv("ROLE_MODEL_CUSTOMIZE_SERVICE_URL",
                                             "http://role_model_customize_service:5000")


def post_persona_matrix(model_student_id: str, portrait_design: list[str]):
    url = f"{role_model_customize_service_url}/PortraitDesign/v1"
    payload = {
        "modelStudentId": model_student_id,
        "portraitDesign": portrait_design
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    return response.json()


def post_knowledge_level(model_student_id: str, knowledge_domain: str, knowledge_level: float):
    url = f"{role_model_customize_service_url}/KnowledgeLevel/v1"
    payload = {
        "modelStudentId": model_student_id,
        "knowledgeDomain": knowledge_domain,
        "knowledgeLevel": knowledge_level
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    return response.json()


# {"category":"RoleModel","page": 1,"pageSize":20}
def get_role_model_customize_list(category: str = "RoleModel", page: int = 1, page_size: int = 20):
    url = f"{role_model_customize_service_url}/RoleModel/v1"
    payload = {
        "category": category,
        "page": page,
        "pageSize": page_size
    }
    response = requests.request("GET", url, json=payload)
    return response.json()
#     mock_data = [
#     {
#         "modelStudentId": "daff9f4f-82a9-34ab-c5da-b88ac70409f5",
#         "人格": "外倾性",
#         "价值观": "享乐主义",
#         "智能": "运动",
#         "领导风格": "教练",
#         " 知识边界": "K2"
#     },
#     {
#         "modelStudentId": "7a435123-a373-7379-f01d-c12a6c43fa8b",
#         "人格": "神经质",
#         "价值观": "利己主义",
#         "智能": "视觉空间",
#         "领导风格": "命令",
#         " 知识边界": "K3"
#     },
#     {
#         "modelStudentId": "f17115e1-b786-edbc-7f6d-34699f1df7e0",
#         "人格": "宜人性",
#         "价值观": "普世主义",
#         "智能": "人际沟通",
#         "领导风格": "关系",
#         " 知识边界": "K4"
#     },
#     {
#         "modelStudentId": "fcb983b9-6f21-272d-fd74-eaa9fca637d2",
#         "人格": "责任心",
#         "价值观": "爱国主义",
#         "智能": "运动",
#         "领导风格": "民主",
#         " 知识边界": "K5"
#     },
#     {
#         "modelStudentId": "081ca4a3-3689-1c17-9cea-c9694716468a",
#         "人格": "责任心",
#         "价值观": "环保主义",
#         "智能": "自然观察",
#         "领导风格": "示范",
#         " 知识边界": "K6"
#     },
#     {
#         "modelStudentId": "75dd0a11-66eb-e57b-c6d5-ad20efdd6a65",
#         "人格": "开放性",
#         "价值观": "享乐主义",
#         "智能": "音乐",
#         "领导风格": "示范",
#         " 知识边界": "K7"
#     },
#     {
#         "modelStudentId": "d2165fad-9959-064f-8351-9912e56203a6",
#         "人格": "神经质",
#         "价值观": "怀疑论",
#         "智能": "视觉空间",
#         "领导风格": "命令",
#         " 知识边界": "K8"
#     },
#     {
#         "modelStudentId": "fc8ba0e2-08d3-9387-495f-3388943b8a40",
#         "人格": "开放性",
#         "价值观": "理性主义",
#         "智能": "逻辑",
#         "领导风格": "远见",
#         " 知识边界": "K9"
#     },
#     {
#         "modelStudentId": "62b1a9af-7403-5cf3-81ff-7b2286d73632",
#         "人格": "宜人性",
#         "价值观": "利他主义",
#         "智能": "人际沟通",
#         "领导风格": "关系",
#         " 知识边界": "K10"
#     },
#     {
#         "modelStudentId": "c83492d5-3688-0ebf-0be8-a1785d53098c",
#         "人格": "责任心",
#         "价值观": "普世主义",
#         "智能": "言语",
#         "领导风格": "远见",
#         " 知识边界": "K11"
#     },
#     {
#         "modelStudentId": "64edc57a-581a-4b3f-049a-6a3d4b89b238",
#         "人格": "责任心",
#         "价值观": "普世主义",
#         "智能": "言语",
#         "领导风格": "远见",
#         " 知识边界": "K12"
#     }
# ]
#     return mock_data
