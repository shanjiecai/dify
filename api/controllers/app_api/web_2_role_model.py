import json

import requests
import streamlit as st

# url_base = "http://127.0.0.1:5001"
url_base = "http://54.193.59.10"
dj_app_id = "a756e5d2-c735-4f68-8db0-1de49333501c"

st.title("role model group chat")
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
        if "4" in app["name"]:
            app_id_list.append(app["id"])
            app_name_list.append(app["name"])
    return app_id_list, app_name_list


if "role_model_id_list" not in st.session_state:
    st.session_state.role_model_id_list = []
    st.session_state.role_name_list = []
if "user" not in st.session_state:
    st.session_state.user = None
if "need_dj" not in st.session_state:
    st.session_state.need_dj = False


app_id_list, app_name_list = get_app_list()

# if len(st.session_state.role_model_id_list) == 0:
    # print(app_name_list)
app_names_select = st.multiselect("Select role models", app_name_list)
need_dj = st.checkbox("need dj")

print(app_names_select)
if need_dj:
    st.session_state.role_name_list.append("James Corden")
    st.session_state.role_model_id_list.append(dj_app_id)

if st.button("choose role models"):

    for app_name in app_names_select:
        app_id = app_id_list[app_name_list.index(app_name)]
        st.session_state.role_model_id_list.append(app_id)
        st.session_state.role_name_list.append(app_name)

st.markdown("Current role model: " + "    ".join(st.session_state.role_name_list))

# 展示当前的角色

if not st.session_state.user:
    user = st.text_input("Enter your name and AI will introduce themselves to you")
    st.session_state.user = user

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


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


# url_base = "http://127.0.0.1:5001"
# role_model_id_list = ["da780e5e-a130-4567-b1cc-b090d59a1d9f", "1e2e3275-216b-4c2b-9b16-53435b72a85a"]
# role_name_list = ["Mauro Gutiérrez", "Lili Tombe"]


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
    print(f"add message {response.text}")
    return


def chat_message_active(app_id, conversation_id, force=False):
    if not force:
        url = f"{url_base}/backend-api/v1/chat-messages-active"
    else:
        url = f"{url_base}/backend-api/v1/chat-messages"

    payload = json.dumps({
        "app_id": app_id,
        "conversation_id": conversation_id,
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


if not st.session_state.conversation_id:
    if st.button("Start conversation and role model will introduce themselves first"):
        role_name_list = st.session_state.role_name_list
        role_model_id_list = st.session_state.role_model_id_list
        user = st.session_state.user
        st.session_state.conversation_id = create_conversation()

        # 开场白
        prompt = f"Hi, I'm {user}, please introduce yourself, @{' @'.join(role_name_list)}"
        st.session_state.messages.append({"role": user, "content": prompt})
        add_message(st.session_state.conversation_id, prompt, user)

        for index, role_name in enumerate(role_name_list):
            print(role_name)
            assistant1_response = chat_message_active(role_model_id_list[index], st.session_state.conversation_id,
                                                      force=True)
            if assistant1_response is not None:
                # with st.chat_message(role_name):
                #     message_placeholder = st.empty()
                #     message_placeholder.markdown(assistant1_response)
                st.session_state.messages.append({"role": role_name, "content": assistant1_response})


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    if st.session_state.conversation_id:
        user = st.session_state["user"]
        role_name_list = st.session_state.role_name_list
        role_model_id_list = st.session_state.role_model_id_list
        print(role_name_list)
        # Add user message to chat history
        print(prompt)
        st.session_state.messages.append({"role": user, "content": prompt})
        add_message(st.session_state.conversation_id, prompt, "Sjc")
        # Display user message in chat message container
        with st.chat_message(user):
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
            # print(st.session_state.messages[-1]["content"])
            force_list = [False for _ in role_name_list]
            # 上一句不是他说的
            for index, role_name in enumerate(role_name_list):
                if f"@{role_name}" in st.session_state.messages[-1]["content"]:
                    force_list[index] = True
            print(f"force_list {force_list}")
            is_anyone_speak = False
            for index, role_name in enumerate(role_name_list):
                print(role_name)
                # 如果上一句是他说的，跳过
                if st.session_state.messages[-1]["role"] == role_name:
                    continue
                assistant1_response = chat_message_active(role_model_id_list[index], st.session_state.conversation_id,
                                                          force=force_list[index])
                if assistant1_response is not None:
                    is_anyone_speak = True
                    with st.chat_message(role_name):
                        message_placeholder = st.empty()
                        message_placeholder.markdown(assistant1_response)
                    st.session_state.messages.append({"role": role_name, "content": assistant1_response})
                    if index == len(role_name_list) - 1:
                        is_new_message = True
            if not is_anyone_speak:
                break
            # if st.session_state.messages[-1]["role"] != role_name_list[1]:
            #     assistant2_response = chat_message_active(role_model_id_list[1], st.session_state.conversation_id)
            #     if assistant2_response is not None:
            #         with st.chat_message(role_name_list[1]):
            #             message_placeholder = st.empty()
            #             message_placeholder.markdown(assistant2_response)
            #         st.session_state.messages.append({"role": role_name_list[1], "content": assistant2_response})
            #         is_new_message = True
    else:
        st.error("Please start conversation first")


