import json
import os
import time

import requests
import spacy

from mylogger import logger

nlp = spacy.load("en_core_web_trf")

app_endpoint = os.getenv("APP_ENDPOINT", "https://www.vvvapp.org")


def get_all_groups(only_dj_bot: bool = False):
    url = f"{app_endpoint}/api/sys/groups"

    payload = {}
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    group_id_list = []
    for i in response.json()['data']:
        if only_dj_bot:
            if i["dj_bot_id"]:
                group_id_list.append(i["id"])
        else:
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


def get_recent_history_within_timestamp(group_id: int = None, start_timestamp: int = None, end_timestamp: int = None):
    res = get_recent_history(group_id)
    # print(res)
    history_all = {"data": []}
    while res['data']:
        break_flag = False
        for i in res['data']:
            if (not start_timestamp or i["timestamp"] >= start_timestamp) and (not end_timestamp or i["timestamp"] <= end_timestamp):
                # print(i["timestamp"])
                history_all["data"].append(i)
            elif i["timestamp"] < start_timestamp:
                break_flag = True
                break
        if break_flag:
            break
        res = get_recent_history(group_id, res['data'][-1]['id'])
    return history_all


def get_recent_history_all_with_last_id(group_id = None, last_id = None):
    res = get_recent_history(group_id)
    history_all = {"data": []}
    while res['data']:
        for i in res['data']:
            if not last_id or i["id"] > int(last_id):
                history_all["data"].append(i)
            else:
                break
        # history_all["data"] += res['data']
        res = get_recent_history(group_id, res['data'][-1]['id'])
    # print(len(history_all["data"]))
    return history_all["data"]


def send_chat_message(group_id: int, message: str = None, type: str = "txt", file_uuid: str = None):
    url = f"{app_endpoint}/api/sys/send_chat_message"

    if type == "img" and file_uuid:
        payload = json.dumps({
            "group_id": group_id,
            "type": type,
            "file_uuid": file_uuid
        })
    else:
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


def upload_file(file_path: str, file_name: str):
    url = f"{app_endpoint}/api/sys/upload"
    payload = {}
    files = [
        ('file', (file_name, open(file_path, 'rb'), 'image/jpeg'))
    ]
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
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


def split_and_get_interval(text):
    begin = time.time()
    doc = nlp(text)
    sentence_list = []
    interval_list = []
    sentences = [sent.text for sent in doc.sents]
    for index, sentence in enumerate(sentences):
        # print(sentence)
        sentence_list.append(sentence)
        if index < len(sentences) - 1:
            # 假设每秒打字速度为15个字
            interval_list.append(round(len(sentences[index+1]) / 7, 1))
    print(time.time() - begin)
    return sentence_list, interval_list


if __name__ == '__main__':
    # print(app_endpoint)
    # print(get_recent_history_within_timestamp(312, 1705709751592, 1706049943669))
    # s = "James Corden: Alright folks, let's make this chat pop like bubble wrap.let's hhhhhhhhhhhhhhhhhhhhhhhhhhhhhh! What's tickling your fancy these days? What's that one thing you can't get enough of? Let's hear it, I'm all ears! 🎤😄"
    # print(split_and_get_interval(s))
    print(get_recent_history_all_with_last_id(316, 17999))
    pass
