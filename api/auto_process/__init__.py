# -*- coding: utf-8 -*-
import requests
import os
from openai import OpenAI

client = OpenAI()
import tiktoken
from auto_process.dataset import get_file_list, create_dataset, upload_file

encode_model = tiktoken.get_encoding("cl100k_base")


# 调用openai总结上传文本
def summarize_text_recursive(name, text, max_length=80):
    if len(text) > 5000:
        text = text[:5000] + '...'
    system_prompt = "You are an advanced AI language model capable of Summarize the character’s personality traits, Because the character information may be too long，therefore You will be provided part of the profile information and previously summarized character traits. Please summarize the character’s personality traits based on the provided information and previously summarized character traits. \n\nBased on the above content, summarize this person’s personality characteristics as briefly as possible in 80 words or less"
    text = f'''{text}\nBased on the above content, summarize this person’s personality characteristics as briefly as possible in {max_length} words or less:\n{name} '''
    messages = [{
        "role": "user",
        "content": text
    }]
    response = client.chat.completions.create(model="gpt-4-1106-preview",
                                              messages=messages,
                                              # temperature=0.3,
                                              max_tokens=max_length + 50,
                                              temperature=0.8,
                                              top_p=0.9,
                                              presence_penalty=0.1,
                                              frequency_penalty=0.1
                                              # top_p=1,
                                              # frequency_penalty=0,
                                              # presence_penalty=0,
                                              # stop=["\n"])
                                              )
    result = ''
    for choice in response.choices:
        result += choice.message.content
    return result


def summarize_text(name, text, max_length=80):
    if len(text) > 5000:
        text = text[:5000] + '...'
    text = f'''{text}\nBased on the above content, summarize this person’s personality characteristics as briefly as possible in {max_length} words or less:\n{name} '''
    messages = [{
        "role": "user",
        "content": text
    }]
    response = client.chat.completions.create(model="gpt-4-1106-preview",
                                              messages=messages,
                                              # temperature=0.3,
                                              max_tokens=max_length + 50,
                                              temperature=0.8,
                                              top_p=0.9,
                                              presence_penalty=0.1,
                                              frequency_penalty=0.1
                                              # top_p=1,
                                              # frequency_penalty=0,
                                              # presence_penalty=0,
                                              # stop=["\n"])
                                              )
    result = ''
    for choice in response.choices:
        result += choice.message.content
    return result


# 总结说话风格
def summarize_style(name, text, max_length=8):
    if len(text) > 4000:
        text = text[:4000] + '...'
    text = f'''{text}\nBased on the above content, summarize this person’s speaking style as briefly as possible in {max_length} words or less:\n{name} '''
    messages = [{
        "role": "user",
        "content": text
    }]
    response = client.chat.completions.create(model="gpt-4-1106-preview",
                                              messages=messages,
                                              # temperature=0.3,
                                              max_tokens=max_length + 50,
                                              temperature=0.2,
                                              top_p=0.7,
                                              presence_penalty=0.1,
                                              frequency_penalty=0.1
                                              # top_p=1,
                                              # frequency_penalty=0,
                                              # presence_penalty=0,
                                              # stop=["\n"])
                                              )
    result = ''
    for choice in response.choices:
        result += choice.message.content
    return result


def generate_character_traits(text, previous_summary):
    # 调用openai总结上传文本
    pass


def process_text(text, summary=""):
    MAX_LENGTH = 8000  # 设定每次处理的最大文本长度

    # 如果文本长度小于最大长度，直接处理
    if len(text) <= MAX_LENGTH:
        new_summary = generate_character_traits(text, summary)  # 生成性格特征
        return new_summary
    else:
        # 如果文本长度超过最大长度，分段处理
        part = text[:MAX_LENGTH]  # 截取前8000个字符
        remaining_text = text[MAX_LENGTH:]  # 保留剩余文本

        new_summary = generate_character_traits(part, summary)  # 生成当前段落的性格特征
        return process_text(remaining_text, new_summary)  # 递归处理剩余文本


if __name__ == '__main__':
    path = "/Users/jiecai/PycharmProjects/dify/api/auto_process/5"
    file_list = os.listdir(path)
    for file in file_list:
        file_path = os.path.join(path, file)
        text = open(file_path, 'r', encoding="gb18030", errors='ignore').read()
        name = file_path.split('/')[-1].split('.')[0]
        # print("*************")
        print(name)
        print(summarize_text(name, text))
        # print("*************")
        print(summarize_style(name, text))
    # file_path = "/Users/jiecai/PycharmProjects/dify/api/auto_process/1/Mallory Asis.txt"
    # text = open(file_path, 'r', errors='ignore').read()
    # name = file_path.split('/')[-1].split('.')[0]
    # print(summarize_text(name, text))
