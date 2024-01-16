import streamlit as st
import requests
import json
url_base = "http://127.0.0.1:5001"
import requests
import json
import os
# from mylogger import logger
app_endpoint = os.getenv("APP_ENDPOINT", "https://www.vvvapp.org")


def get_all_groups():
    url = f"{app_endpoint}/api/sys/groups"

    payload = {}
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    group_id_list = []
    for i in response.json()['data']:
        # if i["dj_bot_id"]:
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

# 映射
model_name_dict = {
    "DJ Bot": "James Corden",
}


# 映射
def model_name_transform(model_name: str):
    if model_name in model_name_dict:
        return model_name_dict[model_name]
    return model_name


def get_summarized_text(prompt, system_prompt, kwargs):
    url = f"{url_base}/backend-api/v1/summarize"
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f',
        'Content-Type': 'application/json'
    }
    data = {
        # "text": text
        "prompt": prompt,
        "system_prompt": system_prompt,
        "kwargs": {"max_tokens": 100}
    }
    data = json.dumps(data)
    response = requests.post(url, headers=headers, data=data)
    return response.json()["result"]


group_id = st.sidebar.selectbox("Select group", get_all_groups())
if group_id:
    st.session_state.group_id = group_id
    recent_history = get_recent_history(group_id=group_id)
    recent_history['data'].reverse()
    history_str = ""
    for message in recent_history['data'][:min(50, len(recent_history['data']))]:
        # outer_memory.append({"role": model_name_transform(message["from_user"]["name"]), "message": message['chat_text']})
        # role:content\n
        # print(message)
        if message['chat_text']:
            message['chat_text'].replace("\n", " ")
        history_str += f"{model_name_transform(message['from_user']['name'])}:{message['chat_text']}\n\n"
    # print(history_str)
    st.text(history_str)
    st.session_state.history_str = history_str

st.session_state.prompt = "Summarize the following text:\n{text}\n\nSummary in 50 words:"
if prompt := st.text_input("prompt", value="Summarize the following text:\n{text}\n\nSummary in 50 words:"):
    st.session_state.prompt = prompt

st.session_state.system_prompt = "You are a highly intelligent chatbot that can summarize text.\n"
if system_prompt := st.text_input("system_prompt", value="You are a highly intelligent chatbot that can summarize text.\n"):
    st.session_state.system_prompt = system_prompt

st.session_state.kwargs = {"max_tokens": 100}
if max_tokens := st.number_input("max_tokens", value=100):
    st.session_state.kwargs["max_tokens"] = max_tokens

if temperature := st.number_input("temperature", value=0.7):
    st.session_state.kwargs["temperature"] = temperature

if top_p := st.number_input("top_p", value=0.7):
    st.session_state.kwargs["top_p"] = top_p

if st.button("Summarize") and st.session_state.history_str:
    st.session_state.summarized_text = get_summarized_text(
        prompt=st.session_state.prompt.format(text=st.session_state.history_str),
        system_prompt=st.session_state.system_prompt,
        kwargs=st.session_state.kwargs
    )
    st.write(st.session_state.summarized_text)
    st.write("Summarized!")




