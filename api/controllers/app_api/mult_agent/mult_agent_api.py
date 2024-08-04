import json
import time

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from knowledge_limit import *
from mult_agent import *

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/knowledge_limit')
async def knowledge_limit(r_json:dict):
    query = r_json.get('query', '')
    # knowledge = r_json.get('knowledge', '')
    knowledge_path = r_json.get('knowledge_path', [])
    t0 = time.time()
    # type = list
    query_kp = json.loads(query_check_and_knowledge_point(query))
    t1 = time.time()
    result = output_judge_result(query_kp, knowledge_path)
    t2 = time.time()
    print(result)
    result = json.loads(result)
    print(f"flag: {result['flag']}\n")

    # 计算时间差
    time_diff1 = t1 - t0
    time_diff2 = t2 - t1
    time_diff = t2 - t0
    # 输出时长，保留小数点后1位
    print(f"query提取知识点时长: {time_diff1:.1f} 秒")
    print(f"知识边界提取知识时长: {time_diff2:.1f} 秒")
    print(f"用户提问到回答总时长: {time_diff:.1f} 秒")
    return result



@app.post('/mult_agent')
async def api(r_json:dict):
    mbti = r_json.get('mbti', '')
    query = r_json.get('query', '')
    history_str= r_json.get('history_str', '')
    description = r_json.get('description', '')
    habbit = r_json.get('habbit', '')
    values_deal = r_json.get('values_deal', '')
    big5 = r_json.get('big5', [])
    knowledge_flag = r_json.get('knowledge_flag', 1)

    result = Role_play(Big5=big5,MBTI=mbti, query={'query': query, 'history': history_str}, Profile=description,
                   Topic_prefer=habbit, Values=values_deal, Flag=knowledge_flag)
    return {'code':0,'data':result}

@app.post('/knowledge_deal')
async def knowledge_deal(r_json:dict):
    knowledge = r_json.get('knowledge', '')
    knowedge_path = create_knowledge_path(knowledge)
    return  {'code':0,'data':knowedge_path}

if __name__ == '__main__':
    # 整体测试
    # input = "hello"
    # input = "I want a hugging from you"
    # input = "I feel very bored and don't know what to do."
    # # input = "heartbreaking for some one leaving me"
    # # input = "how can i do this job successfully, it's too difficult"
    # # input = "how can i do this job successfully, about break up, and how to deal with the emotion after break up"
    # t1 =time.time()
    # r= process(input,[],'')
    # print(time.time()-t1)
    # print(r)
    uvicorn.run(app = "mult_agent_api:app", host = "0.0.0.0", port = 7001,reload = True, timeout_keep_alive = 100, workers = 2,)



