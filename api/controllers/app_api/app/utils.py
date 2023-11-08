import requests
import json


def get_all_groups():
    url = "https://rm.triple3v.org/api/sys/groups"

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


def get_recent_history(group_id: int=None, last_id: int=None):
    url = "https://rm.triple3v.org/api/sys/chat_messages"

    payload = {}
    headers = {
      'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
    }
    if group_id or last_id:
        url += "?"
    if group_id:
        url += "group_id="+str(group_id)+"&"
    if last_id:
        url += "last_id="+str(last_id)+"&"

    response = requests.request("GET", url, headers=headers, data=payload)

    # print(response.text)
    return response.json()


def send_chat_message(group_id: int, message: str):
    url = "https://rm.triple3v.org/api/sys/send_chat_message"

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