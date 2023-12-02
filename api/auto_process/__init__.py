# -*- coding: utf-8 -*-
import requests
import os
import openai
import tiktoken
from auto_process.dataset import get_file_list, create_dataset, upload_file
encode_model = tiktoken.get_encoding("cl100k_base")


# 调用openai总结上传文本
def summarize_text(name, text, max_length=80):
    if len(text) > 4000:
        text = text[:4000] + '...'
    text = f'''{text}\nBased on the above content, summarize this person’s personality characteristics as briefly as possible in {max_length} words or less:\n{name} '''
    messages = [{
        "role": "user",
        "content": text
    }]
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=messages,
        # temperature=0.3,
        max_tokens=max_length+50,
        temperature=0.8,
        top_p=0.9,
        presence_penalty=0.1,
        frequency_penalty=0.1
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0,
        # stop=["\n"]
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
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
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
        # stop=["\n"]
    )
    result = ''
    for choice in response.choices:
        result += choice.message.content
    return result


if __name__ == '__main__':
    path = "/Users/jiecai/PycharmProjects/dify/api/auto_process/4"
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





