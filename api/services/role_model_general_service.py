import os

import requests

role_model_general_service_url = os.getenv("ROLE_MODEL_GENERAL_SERVICE_URL",
                                           "http://106.13.33.123:8000")


# 1	modelStudentId	模范生编码	String
# 2	points	知识点	String
# 3	synonyms	相似词	List
def role_model_general_chat(model_student_id: str, points: str, synonyms: list[str]):
    url = f"{role_model_general_service_url}/chat/v1"
    payload = {
        "modelStudentId": model_student_id,
        "points": points,
        "synonyms": synonyms
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    return response.json()


def role_model_general_personality(model_student_id: str):
    url = f"{role_model_general_service_url}/personality/v1"
    payload = {
        "modelStudentId": model_student_id
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    return response.json()


# 功能概述：获取模范生-人设-知识边界的关系数据
# 请求方式：GET
# 接口地址：http://106.13.33.123:8000/RoleModel/v1
# 请求参数
# 序号	参数名称	参数说明	类型	备注
# 1	category	类别	String
# 2	page	页数	Int
# 3	pageSize	数量	int


def role_model_general_list(category: str = "RoleModel", page: int = 1, page_size: int = 20):
    url = f"{role_model_general_service_url}/RoleModel/v1"
    payload = {
        "category": category,
        "page": page,
        "pageSize": page_size
    }
    response = requests.request("GET", url, json=payload)
    return response.json()
