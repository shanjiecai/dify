import json
import os
import re
import time

import requests


def query_check_and_knowledge_point(input_txt: str):
    # 设置 OpenAI API 密钥
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    sys_prompt = """
You are a knowledgeable assistant, who can accurately diagnose the knowledge points in the input content, and can accurately provide hierarchical subcategories of knowledge points. 

If the query from user's input is just a general chat or private , which only involves some common senses, no special knowledge points in some certain field. Set the chat_flag as 1, and output a json {"chat_flag":1} directly.

If special knowledge points included, Set the chat_flag as 0, and let's think step by step:

1. Give one main knowledge point in {input_txt}
2. Give the top category which the knowledge point belongs to. The top category shall be one of the list: ['LifeSciences', 'Physics', 'Chemistry', 'Mathematics', 'Astronomy', 'EarthScience', 'Anthropology', 'Archaeology', 'Sociology', 'Economics', 'Politics', 'Military', 'Education', 'Law&Justice', 'Psychology', 'EngineeringTechnology', 'History', 'Geography', 'Philosophy&Religion', 'Humanities&Arts', 'Sports&Entertainment']
3. Give the hierarchical subcategories from top category to the knowledge point. The subcategories shall be in a string separated by slashes, which begins with top category, and ends with the knowledge point, and each item shall be the direct subcategory of the previous item.

【Output format】
The {output} shall be in a json format, and contain 3 main keys.

【Example 1】
{input_txt}:
How do you stay motivated and focused during a tough game or when facing a losing streak?
{output}:
{"chat_flag":1}

【Example 2】
{input_txt}:
Can you explain the direction of current for me?
{output}:
{"chat_flag":0, "knowledge_point": "Current Direction", "top_category": "Physics",
 "subcategories": "Physics/Electricity and Magnetism/Electric Current/Current Direction"}

【Example 3】
{input_txt}:
I like a famous Chinese novel: Journey to the West.
{output}:
{"chat_flag":0, "knowledge_point": "Journey to the West", "top_category": "Humanities&Arts",
 "subcategories": "Humanities&Arts/Literature/Chinese Literature/Classical Chinese Novels/Chinese Supernatural Novel/Journey to the West"}

【restrictions】
Dont't output anything out of json structure (Very important)
"""

    messages_list = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": input_txt},
    ]

    data = {
        "model": "gpt-4o-mini",
        "messages": messages_list,
        "temperature": 0,  # 控制输出确定性
        "response_format": {"type": "json_object"}  # 控制输出为json
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']


# 知识边界klimit，但是划分为list后需要逐项调用openai，效率较低，
def pre_process_klimit(input: str):
    # 使用正则表达式匹配括号内的内容
    pattern = r'\([^()]*\)'
    # 使用正则表达式替换括号内的逗号为一个特殊标记，例如 "##COMMA##"
    modified_input = re.sub(pattern, lambda m: m.group(0).replace(',', '##COMMA##'), input)
    # 分割字符串为列表
    result = modified_input.split(',')
    # 将特殊标记替换回逗号
    result = [item.replace('##COMMA##', ',') for item in result]
    return result


url = "https://api.openai.com/v1/chat/completions"
api_key = os.getenv("OPENAI_API_KEY")


# 查询用户输入的查询包含哪个知识点
def query_knowledge_point(input_txt: str):
    # 设置 OpenAI API 密钥
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    sys_prompt = """
You are a knowledgeable assistant, who can accurately diagnose the knowledge points in the input content, and can accurately provide hierarchical subcategories of knowledge points. 

Let's think step by step:

1. Give one main knowledge point in {input_txt}
2. Give the top category which the knowledge point belongs to. The top category shall be one of the list: ['LifeSciences', 'Physics', 'Chemistry', 'Mathematics', 'Astronomy', 'EarthScience', 'Anthropology', 'Archaeology', 'Sociology', 'Economics', 'Politics', 'Military', 'Education', 'Law&Justice', 'Psychology', 'EngineeringTechnology', 'History', 'Geography', 'Philosophy&Religion', 'Humanities&Arts', 'Sports&Entertainment']
3. Give the hierarchical subcategories from top category to the knowledge point. The subcategories shall be in a string separated by slashes, which begins with top category, and ends with the knowledge point, and each item shall be the direct subcategory of the previous item.

【Output format】
The {output} shall be in a json format, and contain 3 main keys.

【Example 1】
{input_txt}:
Can you explain the direction of current for me?
{output}:
{"knowledge_point": "Current Direction", "top_category": "Physics",
 "subcategories": "Physics/Electricity and Magnetism/Electric Current/Current Direction"}

【Example 2】
{input_txt}:
I like a famous Chinese novel: Journey to the West.
{output}:
{"knowledge_point": "Journey to the West", "top_category": "Humanities&Arts",
 "subcategories": "Humanities&Arts/Literature/Chinese Literature/Classical Chinese Novels/Chinese Supernatural Novel/Journey to the West"}

【restrictions】
Dont't output anything out of json structure (Very important)
"""

    messages_list = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": input_txt},
    ]

    data = {
        "model": "gpt-4o-mini",
        "messages": messages_list,
        "temperature": 0,  # 控制输出确定性
        "response_format": {"type": "json_object"}  # 控制输出为json
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']


# 多进程并行提取知识层次
import multiprocessing
from concurrent.futures import ProcessPoolExecutor


def GPT_detect(input_txt, shared_list):
    output1 = query_knowledge_point(input_txt)
    text = json.loads(output1)
    shared_list.append(text)


# 循环调用，并行处理
def multi_process_knowledge_points(input_list):
    # 待写入的共享list
    manager = multiprocessing.Manager()
    shared_list = manager.list()

    # Get CPU core count
    cpu_count = multiprocessing.cpu_count()
    executor = ProcessPoolExecutor(max_workers=3)

    # Submit tasks to the executor （异步执行，若单进程耗时长，也不拥堵）
    for input_txt in input_list:
        executor.submit(GPT_detect, input_txt, shared_list)

    executor.shutdown()

    return list(shared_list)


# 判断能否回答用户的问题
def judge_knowledge_ability(query_kp_path, relate_kps_path):
    # 设置 OpenAI API 密钥
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    sys_prompt = f'''
You are a knowledgeable assistant, who can judge whether your can answer the question with knowledge in <query_kp_path>,  based on the knowlege <relate_kps_path> you have learned.

query_kp_path = {query_kp_path}
relate_kps_path = {relate_kps_path}

Let's think step by step:

1. whether <query_kp_path> has related subcategory with items of <relate_kps_path>. If related, 'related'=1, else 0.
2. whether <query_kp_path> is subcategory of one of <relate_kps_path>. If true, 'contained'=1, else 0.
3. whether <query_kp_path> shall be learned in advance,  if <relate_kps_path> have been learned. If true, 'pre_kp'=1, else 0.
4. whether <query_kp_path> is easier than the items in <relate_kps_path>. If true, 'easier'=1,  else 0.
5. whether the knowlege level of <query_kp_path> is lower than the items in <relate_kps_path>. If true, 'lower_level'=1, else 0.

And then based on the analysis, judge whether your can answer the question with knowledge in <query_kp_path>. If true, 'flag'=1, else 0.

【Output format】
The output shall be in a json format, and contain the main keys below: 
'flag', 'related', 'contained', 'pre_kp', 'easier', 'lower_level'

【restrictions】
Dont't output anything out of json structure (Very important)
'''

    messages_list = [
        {"role": "system", "content": sys_prompt},
    ]

    data = {
        "model": "gpt-4o-mini",
        "messages": messages_list,
        "temperature": 0,  # 控制输出确定性
        "response_format": {"type": "json_object"}  # 控制输出为json
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']


def create_knowledge_path(knowledge:str):
    limits_list = pre_process_klimit(knowledge)
    limits_kps = multi_process_knowledge_points(limits_list)
    limits_kps_path = [item['subcategories'] for item in limits_kps if 'subcategories' in item]
    return limits_kps_path


def output_judge_result(query_kp, limits_kps_path):
    if query_kp['chat_flag']==1:
        return '{"flag":1}'
    else:
        query_kp_path = query_kp['subcategories']
        decision = judge_knowledge_ability(query_kp_path, limits_kps_path)
        return decision

# ========
# test
# ========
if __name__ == '__main__':

    query = "Can you explain the direction of current for me?"

    limits_input = "Trigonometric functions,Probability and statistics ,Kinematics equations (motion in two dimensions),Newton's laws of motion and force diagrams, Conservation of energy and momentum,Basic circuits (Ohm's law, series and parallel circuits),Wave properties and behaviors,Balancing chemical equations,Stoichiometry calculations,Basic organic chemistry nomenclature,Cell structure and function,DNA replication and protein synthesis, Mendelian genetics and Punnett squares"

    t0 = time.time()
    limits_list = pre_process_klimit(limits_input)
    # type = list
    query_kp = json.loads(query_knowledge_point(query))
    t1 = time.time()
    limits_kps = multi_process_knowledge_points(limits_list)
    t2 = time.time()

    query_kp_path = query_kp['subcategories']
    limits_kps_path = [item['subcategories'] for item in limits_kps if 'subcategories' in item]

    decision = judge_knowledge_ability(query_kp_path, limits_kps_path)
    # 返回 json.loads(decision)['flag']
    t3 = time.time()

    print(f"flag: {json.loads(decision)['flag']}\n")

    # 计算时间差
    time_diff1 = t1 - t0
    time_diff2 = t2 - t1
    time_diff3 = t3 - t2
    time_diff = t3 - t0
    # 输出时长，保留小数点后1位
    print(f"query提取知识点时长: {time_diff1:.1f} 秒")
    print(f"知识边界提取知识时长: {time_diff2:.1f} 秒")
    print(f"判断分身能否回答时长: {time_diff3:.1f} 秒")
    print(f"用户提问到回答总时长: {time_diff:.1f} 秒")

    '''
    query提取知识点时长: 0.6 秒
    知识边界提取知识时长: 1.9 秒
    判断分身能否回答时长: 0.6 秒
    用户提问到回答总时长: 3.2 秒
    '''

