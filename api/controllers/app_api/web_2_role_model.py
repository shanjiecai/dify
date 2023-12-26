import streamlit as st
import random
import time
import requests
import json
url_base = "http://13.56.164.188"
dj_app_id = "a756e5d2-c735-4f68-8db0-1de49333501c"


def get_app_list():
    global app_name_select
    url = f"{url_base}/backend-api/v1/app/list"

    payload = {}
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    # print(response.text)
    app_id_list = [app["app_id"] for app in response.json()["app_list"]]
    app_name_list = [app["app_name"] for app in response.json()["app_list"]]
    return app_id_list, app_name_list


if "role_model_id_list" not in st.session_state:
    app_id_list, app_name_list = get_app_list()
    app_name_select = st.selectbox("Select role model", app_name_list, key="role_model_id_list")
    app_id_select = app_id_list[app_name_list.index(app_name_select[0])]
    st.session_state["role_model_id_list"] = [dj_app_id, app_id_select]
    st.session_state["role_name_list"] = ["DJ Bot", app_name_select]

# url_base = "http://127.0.0.1:5001"
# role_model_id_list = ["da780e5e-a130-4567-b1cc-b090d59a1d9f", "1e2e3275-216b-4c2b-9b16-53435b72a85a"]
# role_name_list = ["Mauro Gutiérrez", "Lili Tombe"]

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

    return response.json()["conversation_id"]


def add_message(conversation_id, message, user):
    url = f"{url_base}/backend-api/v1/conversations/add_message"

    payload = json.dumps({
        "message": message,
        "conversation_id": conversation_id,
        "user": user,
        "app_id": dj_app_id,
    })
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f',
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    return


def chat_message_active(app_id, conversation_id):
    url = f"{url_base}/backend-api/v1/chat-messages-active"

    payload = json.dumps({
        "app_id": app_id,
        "conversation_id": conversation_id,
    })
    headers = {
        'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    if response.json()["result"]:
        return response.json()["answer"]
    else:
        return None


if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = create_conversation()


st.title("2 role model chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    role_name_list = st.session_state["role_name_list"]
    role_model_id_list = st.session_state["role_model_id_list"]
    # Add user message to chat history
    st.session_state.messages.append({"role": "Sjc", "content": prompt})
    add_message(st.session_state.conversation_id, prompt, "Sjc")
    # Display user message in chat message container
    with st.chat_message("Sjc"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    # with st.chat_message("Tom"):
    #     message_placeholder = st.empty()
    #     full_response = ""
    #     assistant_response = random.choice(
    #         [
    #             "Hello there! How can I assist you today?",
    #             "Hi, human! Is there anything I can help you with?",
    #             "Do you need help?",
    #         ]
    #     )
    #     # Simulate stream of response with milliseconds delay
    #     for chunk in assistant_response.split():
    #         full_response += chunk + " "
    #         time.sleep(0.05)
    #         # Add a blinking cursor to simulate typing
    #         message_placeholder.markdown(full_response + "▌")
    #     message_placeholder.markdown(full_response)
    # # Add assistant response to chat history
    # st.session_state.messages.append({"role": "Tom", "content": full_response})
    is_new_message = True
    while is_new_message:
        is_new_message = False
        # 上一句不是他说的
        if st.session_state.messages[-1]["role"] != role_name_list[0]:
            assistant1_response = chat_message_active(role_model_id_list[0], st.session_state.conversation_id)
            if assistant1_response is not None:
                with st.chat_message(role_name_list[0]):
                    message_placeholder = st.empty()
                    message_placeholder.markdown(assistant1_response)
                st.session_state.messages.append({"role": role_name_list[0], "content": assistant1_response})
        if st.session_state.messages[-1]["role"] != role_name_list[1]:
            assistant2_response = chat_message_active(role_model_id_list[1], st.session_state.conversation_id)
            if assistant2_response is not None:
                with st.chat_message(role_name_list[1]):
                    message_placeholder = st.empty()
                    message_placeholder.markdown(assistant2_response)
                st.session_state.messages.append({"role": role_name_list[1], "content": assistant2_response})
                is_new_message = True


