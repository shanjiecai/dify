import random

import openai
from mylogger import logger

from core.model_providers.models.llm.base import BaseLLM
import tiktoken

encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')

def judge_llm_active(api_key: str, histories: str, assistant_name: str, is_random_true: bool = True):
    if not api_key:
        return False
    openai.api_key = api_key
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
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        max_tokens=1,
        temperature=0,
        presence_penalty=0,
        frequency_penalty=0,
        top_p=1,
        messages=messages,
        stream=False
    )
    # 加入一定概率让能返回True
    if is_random_true and random.random() < 0.2:
        return True
    return response["choices"][0]["message"]["content"].strip().lower().startswith("yes")


if __name__ == '__main__':
    # print(judge_llm_active("", '''''', "James Corden"))
    print(random.random())

