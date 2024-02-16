import json
import random
import traceback

import requests

# from core.model_providers.models.llm.base import BaseLLM
import tiktoken
from openai import OpenAI

from mylogger import logger

encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')  # 暂时没用到

en_prompt = '''You are a robot that can only answer 'yes' or 'no'. Given the conversation history in the group chat, you should answer as {user}, and you can only answer 'yes' or 'no'. Here is the conversation history.
{history}
Should you answer as {user}:'''


def judge_llm_active(api_key: str, histories: str, assistant_name: str, is_random_true: bool = True):
    try:
        histories = histories.replace("(AI)", "").replace("(4)", "").replace("(3.5)", "")
        url = "http://117.50.189.88:19521/generate"

        if assistant_name == "James Corden":
            assistant_name = "James Corden or DJ Bot"
        payload = json.dumps({
            "prompt": en_prompt.format(user=assistant_name, history=histories),
            "use_beam_search": False,
            "temperature": 0,
            "max_tokens": 3
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        logger.info(response.text)
        if response.status_code == 200:
            if "yes" in response.json().text[0]:
                return True
            else:
                return False
        else:
            pass
    except:
        logger.info(f"{traceback.format_exc()}")
        pass
    if not api_key:
        return False
    if assistant_name != "James Corden":
        prompt = f'''You are {assistant_name} in a group chat.
        You need to participate in the group chat. Here is the group chat histories, inside <histories></histories> XML tags.
        <histories>
        {histories}
        </histories>
        You should determine whether to answer as {assistant_name}, just return yes or no
        '''
    else:
        # 主持人prompt，尽量活跃气氛
        prompt = f'''You are {assistant_name} or DJ Bot in a group chat.As the host of the group chat, you need to participate in the group chat and try to liven up the atmosphere.
        Here is the group chat histories, inside <histories></histories> XML tags.
        <histories>
        {histories}
        </histories>
        You should determine whether to answer as {assistant_name} or DJ Bot, just return yes or no
        '''
    logger.info(len(prompt))
    if len(prompt) > 10000:
        prompt = prompt[:10000]

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(model="gpt-3.5-turbo-0125",
    max_tokens=1,
    temperature=0,
    presence_penalty=0,
    frequency_penalty=0,
    top_p=1,
    messages=messages,
    stream=False)
    # 加入一定概率让能返回True
    if is_random_true and random.random() < 0.2:
        return True
    return response.choices[0].message.content.strip().lower().startswith("yes")


if __name__ == '__main__':
    print(judge_llm_active("", '''''', "James Corden"))
    # print(random.random())
