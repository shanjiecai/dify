import requests
import json
import os
from mylogger import logger
app_endpoint = os.getenv("APP_ENDPOINT", "https://rm.triple3v.org")


def get_all_groups():
    url = f"{app_endpoint}/api/sys/groups"

    payload = {}
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    group_id_list = []
    for i in response.json()['data']:
        if i["dj_bot_id"]:
            group_id_list.append(i["id"])
    return group_id_list


def get_triple3v_users_from_ids(ids):
    url = f"{app_endpoint}/api/sys/users?ids=" + ids

    payload = {}
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.json()


def get_recent_history(group_id: int = None, last_id: int = None):
    url = f"{app_endpoint}/api/sys/chat_messages"

    payload = {}
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
    }
    if group_id or last_id:
        url += "?"
    if group_id:
        url += "group_id=" + str(group_id) + "&"
    if last_id:
        url += "last_id=" + str(last_id) + "&"

    response = requests.request("GET", url, headers=headers, data=payload)

    # print(response.text)
    return response.json()


def send_chat_message(group_id: int, message: str):
    url = f"{app_endpoint}/api/sys/send_chat_message"

    payload = json.dumps({
        "group_id": group_id,
        "txt": message
    })
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    return response.json()


feishu_alert_url = os.environ.get("FEISHU_ALERT_URL")
print(feishu_alert_url)


def send_feishu_bot(message):
    data = {"msg_type": "text", "content": {"text": message}}
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(feishu_alert_url, headers=headers, json=data)
    logger.info(response.text)
    return response.json()
