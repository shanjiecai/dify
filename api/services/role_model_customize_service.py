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



