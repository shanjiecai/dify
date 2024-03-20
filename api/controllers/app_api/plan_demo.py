import json
import time

import requests
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

# url_base = "http://54.193.59.10"
url_base = "http://127.0.0.1:5001"
st.set_page_config(
    page_title="Demo",
    page_icon=":robot:",
    layout="wide"
)
# url_base = "http://13.56.164.188"

# from mylogger import logger
# app_endpoint = os.getenv("APP_ENDPOINT", "https://www.vvvapp.org")
#
#
# def get_all_groups():
#     url = f"{app_endpoint}/api/sys/groups"
#
#     payload = {}
#     headers = {
#         'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
#     }
#     response = requests.request("GET", url, headers=headers, data=payload)
#     group_id_list = []
#     for i in response.json()['data']:
#         # if i["dj_bot_id"]:
#             group_id_list.append(i["id"])
#     return group_id_list
#
#
# def get_triple3v_users_from_ids(ids):
#     url = f"{app_endpoint}/api/sys/users?ids=" + ids
#
#     payload = {}
#     headers = {
#         'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
#     }
#
#     response = requests.request("GET", url, headers=headers, data=payload)
#
#     print(response.text)
#     return response.json()
#
#
# def get_recent_history(group_id: int = None, last_id: int = None):
#     url = f"{app_endpoint}/api/sys/chat_messages"
#
#     payload = {}
#     headers = {
#         'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf'
#     }
#     if group_id or last_id:
#         url += "?"
#     if group_id:
#         url += "group_id=" + str(group_id) + "&"
#     if last_id:
#         url += "last_id=" + str(last_id) + "&"
#
#     response = requests.request("GET", url, headers=headers, data=payload)
#
#     # print(response.text)
#     return response.json()
#
# # 映射
# model_name_dict = {
#     "DJ Bot": "James Corden",
# }
#
#
# # 映射
# def model_name_transform(model_name: str):
#     if model_name in model_name_dict:
#         return model_name_dict[model_name]
#     return model_name
#
#
# def get_summarized_text(prompt, system_prompt, kwargs):
#     url = f"{url_base}/backend-api/v1/summarize"
#     headers = {
#         'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f',
#         'Content-Type': 'application/json'
#     }
#     data = {
#         # "text": text
#         "prompt": prompt,
#         "system_prompt": system_prompt,
#         "kwargs": {"max_tokens": 100}
#     }
#     data = json.dumps(data)
#     response = requests.post(url, headers=headers, data=data)
#     print(response.text)
#     return response.json()["result"]
#
#
# group_id = st.sidebar.selectbox("Select group", get_all_groups())
# if group_id:
#     st.session_state.group_id = group_id
#     recent_history = get_recent_history(group_id=group_id)
#     recent_history['data'].reverse()
#     history_str = ""
#     for message in recent_history['data'][:min(50, len(recent_history['data']))]:
#         # outer_memory.append({"role": model_name_transform(message["from_user"]["name"]), "message": message['chat_text']})
#         # role:content\n
#         # print(message)
#         if message['chat_text']:
#             message['chat_text'].replace("\n", " ")
#         history_str += f"{model_name_transform(message['from_user']['name'])}:{message['chat_text']}\n\n"
#     print(json.dumps(history_str, ensure_ascii=False))
#     st.text(history_str)
#     st.session_state.history_str = history_str
#
# # st.session_state.prompt = "Summarize the following text:\n{text}\n\nSummary in 50 words:"
# st.session_state.prompt = "{text}"
# # if prompt := st.text_input("prompt", value="Summarize the following text:\n{text}\n\nSummary in 50 words:"):
# if prompt := st.text_input("prompt", value="{text}"):
#     st.session_state.prompt = prompt
#
# # st.session_state.system_prompt = "You are a highly intelligent chatbot that can summarize text.\n"
# if system_prompt := st.text_input("system_prompt", value=""):
#     st.session_state.system_prompt = system_prompt
#
# st.session_state.kwargs = {"max_tokens": 100}
# if max_tokens := st.number_input("max_tokens", value=100):
#     st.session_state.kwargs["max_tokens"] = max_tokens
#
# if temperature := st.number_input("temperature", value=0.7):
#     st.session_state.kwargs["temperature"] = temperature
#
# if top_p := st.number_input("top_p", value=0.7):
#     st.session_state.kwargs["top_p"] = top_p
#
# if st.button("Summarize") and st.session_state.history_str:
#     st.session_state.summarized_text = get_summarized_text(
#         prompt=st.session_state.prompt.format(text=st.session_state.history_str),
#         system_prompt=st.session_state.system_prompt,
#         kwargs=st.session_state.kwargs
#     )
#     st.write(st.session_state.summarized_text)
#     st.write("Summarized!")


dj_app_id = "a756e5d2-c735-4f68-8db0-1de49333501c"


def create_conversation():
    url = f"{url_base}/backend-api/v1/conversations"

    payload = json.dumps({
        "app_id": dj_app_id
    })
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    return response.json()["conversation_id"]


def chat_message_active(app_id, conversation_id, force=True, query=None):
    if not force:
        url = f"{url_base}/backend-api/v1/chat-messages-active"
    else:
        url = f"{url_base}/backend-api/v1/chat-messages"

    payload = json.dumps({
        "app_id": app_id,
        "conversation_id": conversation_id,
        "query": query,
        "user": "user"
    })
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(f"chat {app_id} {response.text}")
    if response.json().get("answer", None):
        return response.json()["answer"]
    else:
        return None


if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = create_conversation()


def get_app_list():
    global app_name_select
    url = f"{url_base}/backend-api/v1/app/list"

    payload = {}
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    # print(response.text)
    app_id_list = []
    app_name_list = []
    for app in response.json():
        if "(" in app["name"] or "（" in app["name"]:
            continue
        else:
            app_id_list.append(app["id"])
            app_name_list.append(app["name"])
    return app_id_list, app_name_list


def get_conversation_plan_detail(conversation_id):
    import requests

    url = f"http://127.0.0.1:5001/backend-api/v1/conversations/plan/detail/{conversation_id}"

    payload = {}
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.json()


app_id_list, app_name_list = get_app_list()
print(app_name_list)

if "app_id" not in st.session_state or st.session_state.app_name == app_name_list[0]:
    st.session_state.app_name = st.selectbox("Select app", app_name_list)
    print(st.session_state.app_name)
    st.session_state.app_id = app_id_list[app_name_list.index(st.session_state.app_name)]
    print(st.session_state.app_id)

if "history" not in st.session_state:
    st.session_state.history = []
if "past_key_values" not in st.session_state:
    st.session_state.past_key_values = None

# max_length = st.sidebar.slider("max_length", 0, 32768, 8192, step=1)
# top_p = st.sidebar.slider("top_p", 0.0, 1.0, 0.8, step=0.01)
# temperature = st.sidebar.slider("temperature", 0.0, 1.0, 0.6, step=0.01)

buttonClean = st.sidebar.button("清理会话历史", key="clean")
if buttonClean:
    st.session_state.history = []
    st.session_state.past_key_values = None
    st.rerun()

for i, message in enumerate(st.session_state.history):
    if message["role"] == "user":
        with st.chat_message(name="user", avatar="user"):
            st.markdown(message["content"])
    else:
        with st.chat_message(name="assistant", avatar="assistant"):
            st.markdown(message["content"])

with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    message_placeholder = st.empty()

#      if response.endswith("<finish_question>"):
#         while True:
#             res = get_conversation_plan_detail(st.session_state.conversation_id)
#             if res.get("plan_detail_list", None):
#                 for i in res["plan_detail_list"]:
#                     print(i)
#                     message_placeholder.markdown(i)
#                     st.session_state.history.append({"role": "assistant", "content": i})
#                 break
# 另起线程获取计划
import threading


def get_plan():
    while True:
        if "conversation_id" not in st.session_state:
            time.sleep(1)
            continue
        res = get_conversation_plan_detail(st.session_state.conversation_id)
        print(res)
        if res.get("plan_detail_list", None):
            for i in res["plan_detail_list"]:
                message_placeholder.markdown(i)
                st.session_state.history.append({"role": "assistant", "content": i})
            break
        time.sleep(1)


t = threading.Thread(target=get_plan)
ctx = get_script_run_ctx()
add_script_run_ctx(t, ctx)
t.start()

# st.script_run_context.add_script_run_ctx(t)

prompt_text = st.chat_input("请输入您的问题")
if prompt_text:
    input_placeholder.markdown(prompt_text)
    history = st.session_state.history
    # past_key_values = st.session_state.past_key_values
    # for response, history, past_key_values in model.stream_chat(
    #         tokenizer,
    #         prompt_text,
    #         history,
    #         past_key_values=past_key_values,
    #         max_length=max_length,
    #         top_p=top_p,
    #         temperature=temperature,
    #         return_past_key_values=True,
    # ):
    #     message_placeholder.markdown(response)
    response = chat_message_active(st.session_state.app_id, st.session_state.conversation_id, force=True,
                                   query=prompt_text)
    st.session_state.history.append({"role": "user", "content": prompt_text})
    st.session_state.history.append({"role": "assistant", "content": response})
    for i in st.session_state.history:
        message_placeholder.markdown(i)

    # st.session_state.past_key_values = past_key_values
