import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Union

import requests
from flask_restful import reqparse

from controllers.app_api import api
from controllers.app_api.mult_agent.knowledge_limit import (
    create_knowledge_path,
    output_judge_result,
    query_check_and_knowledge_point,
)
from controllers.app_api.mult_agent.mult_agent import *
from controllers.app_api.wraps import AppApiResource
from extensions.ext_database import db
from models.model import App, ModelPerson
from mylogger import logger


def extract_info_with_gemini(values):

    values = ", ".join(values)

    prompts = f"""Act as a personal values generator. Based on the following personal values:[{values}]generate a description of a person's lifestyle , preferences and behaviors that guide their decisions and actions.Provide a short explanation for each value.\nGenerate the list of values in this format:\n1. [Value]: Brief explanation\n2. [Value]: Brief explanation\n...\n\nAfter listing the values, provide a short summary of how these values might influence the person's life decisions and behaviors.\n"""
    json_data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompts
                    }
                ]
            }
        ]
    }

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyCFSd0eKhcDh1p8HxSwQcgjubFJz62YPVU",
        json=json_data)
    response = response.text
    data = json.loads(response)

    try:
        data = data['candidates'][0]['content']['parts'][0]['text']
        return data
    except:
        data = data
        print(data)
        return None


class Create_model_person(AppApiResource):

    def post(self, app_model: App):
        """
        Create or update a model person in the database
        ---
        tags:
          - restful
        parameters:
          - in: body
            name: app_model
            required: true
            description: The app model containing the person's details
            schema:
              properties:
                name:
                  type: string
                  description: The name of the person
                habbit:
                  type: string
                  description: The habit of the person
                values:
                  type: array
                  description: The values associated with the person
                  items:
                    type: string
                values_deal:
                  type: string
                  description: Processed values data
                knowledge:
                  type: string
                  description: Knowledge data
                mbti:
                  type: string
                  description: MBTI personality type
                audio_model_s_path:
                  type: string
                  description: Path to the small audio model
                audio_model_g_path:
                  type: string
                  description: Path to the general audio model
                audio_reference_path:
                  type: string
                  description: Path to the audio reference
                audio_reference_text:
                  type: string
                  description: Text associated with the audio reference
                description:
                  type: string
                  description: A description of the person
                big5:
                  type: array
                  description: Big Five personality traits
                  items:
                    type: string
                appid:
                  type: string
                  description: The application ID (if updating an existing person)
        responses:
          200:
            description: The appid of the created or updated person
            schema:
              type: object
              properties:
                appid:
                  type: string
                  description: The application ID
        """
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=False, location='json', default=None)
        parser.add_argument('habbit', type=str, required=False, location='json', default=None)
        parser.add_argument('values', type=list, required=False, default=[], location='json')
        parser.add_argument('values_deal', type=str, required=False, default=None, location='json')
        parser.add_argument("knowledge", type=str, required=False, location="json", default=None)
        parser.add_argument("mbti", type=str, required=False, location="json", default=None)
        parser.add_argument("audio_model_s_path", type=str, required=False, location="json", default=None)
        parser.add_argument("audio_model_g_path", type=str, required=False, location="json", default=None)
        parser.add_argument("audio_reference_path", type=str, required=False, location="json", default=None)
        parser.add_argument("audio_reference_text", type=str, required=False, location="json", default=None)
        parser.add_argument("audio_reference_path", type=str, required=False, location="json", default=None)
        parser.add_argument("description", type=str, required=False, location="json", default=None)
        parser.add_argument("big5", type=str, required=False, location="json", default=[])
        parser.add_argument("appid", type=str, required=False, location="json", default="")

        # print(11111)
        args = parser.parse_args()

        name = args['name']
        habbit = args['habbit']
        values = args['values']
        values_deal = args['values_deal']
        knowledge = args['knowledge']
        mbti = args['mbti']
        audio_model_s_path = args['audio_model_s_path']
        audio_model_g_path = args['audio_model_g_path']
        audio_reference_path = args['audio_reference_path']
        audio_reference_text = args['audio_reference_text']
        description = args['description']
        big5 = args['big5']
        appid = args['appid']

        if not values_deal:
            if values:
                values_deal = extract_info_with_gemini(values)
            else:
                values_deal = None
        if knowledge:
            url = 'http://13.56.82.62:7000/knowledge_deal'
            body = {'knowledge': knowledge}
            response = requests.post(url, json=body)
            response = response.json()
            knowledge_path = json.dumps(response['data'])
        else:
            knowledge_path = ""
        if appid:
            model_person = db.session.query(ModelPerson).filter(ModelPerson.appid == appid).first()
            if name: model_person.name = name
            if habbit: model_person.habbit = habbit
            if values: model_person.values = json.dumps(values)
            if values_deal: model_person.values_deal = values_deal
            if knowledge: model_person.knowledge = knowledge
            if mbti: model_person.mbti = mbti
            if audio_model_g_path: model_person.audio_model_g_path = audio_model_g_path
            if audio_model_s_path: model_person.audio_model_s_path = audio_model_s_path
            if audio_reference_path: model_person.audio_reference_path = audio_reference_path
            if audio_reference_text: model_person.audio_reference_text = audio_reference_text
            if description: model_person.description = description
            model_person.update_time = datetime.now()
            if big5: model_person.big5 = json.dumps(big5)
            if knowledge_path: model_person.knowledge_path = knowledge_path
            db.session.commit()
            return {'appid': model_person.appid}, 200
        else:
            model_person = ModelPerson()
            model_person.id = str(uuid.uuid4())
            model_person.name = name
            model_person.habbit = habbit
            model_person.values = json.dumps(values)
            model_person.values_deal = values_deal
            model_person.knowledge = knowledge
            model_person.mbti = mbti
            model_person.appid = str(uuid.uuid4())
            model_person.audio_model_g_path = audio_model_g_path
            model_person.audio_model_s_path = audio_model_s_path
            model_person.audio_reference_path = audio_reference_path
            model_person.audio_reference_text = audio_reference_text
            model_person.description = description
            model_person.create_time = datetime.now()
            model_person.update_time = datetime.now()
            model_person.big5 = json.dumps(big5)
            model_person.knowledge_path = knowledge_path
            db.session.add(model_person)
            db.session.commit()

            return {'appid': model_person.appid}, 200


class Mult_agent_talk(AppApiResource):
    def post(self, app_model: App):
        """
        Simulate a multi-agent conversation based on stored profile data
        ---
        tags:
          - restful
        parameters:
          - in: body
            name: app_model
            required: true
            description: The app model containing conversation details
            schema:
              properties:
                appid:
                  type: string
                  description: The application ID to identify the person
                query:
                  type: string
                  description: The query or statement to be processed by the agents
                history:
                  type: array
                  description: Conversation history
                  items:
                    type: string
        responses:
          200:
            description: The response generated by the agents
            schema:
              type: object
              properties:
                answer:
                  type: string
                  description: The generated response
          400:
            description: Error message if appid is invalid or processing fails
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message
        """
        t1 = time.time()
        parser = reqparse.RequestParser()
        parser.add_argument('appid', type=str, required=False, location='json', default=None)
        parser.add_argument('query', type=str, required=False, location='json', default=None)
        parser.add_argument('history', type=list, required=False, location='json', default=[])
        args = parser.parse_args()
        appid = args['appid']
        query = args['query']
        history = args['history']
        history_str = ''
        for i in history:
            history_str += str(i)
        print(appid)
        person = db.session.query(ModelPerson).filter(ModelPerson.appid == appid).first()
        print(person)
        if not person:
            return {'message': "appid不对"}, 400
        print(person.name, person.id, person.mbti, person.knowledge)
        t2 = time.time()
        print('读取数据库时间', t2 - t1)
        # try:
        #     url = 'http://13.56.82.62:7000/knowledge_limit'
        #     body = {"query": query,
        #             "knowledge_path": json.loads(person.knowledge_path),
        #             }
        #     print('知识边界入参',body)
        #     response = requests.post(url=url, json=body)
        #
        #     decision = response.json()
        #     flag =decision['flag']
        # except Exception as e:
        #     print(e)
        #     # return {'message': "知识边界报错" +e}, 400
        #     flag = 1
        query_kp = json.loads(query_check_and_knowledge_point(query))
        result = output_judge_result(query_kp, json.loads(person.knowledge_path))
        result = json.loads(result)
        flag = result['flag']
        print(flag)
        t3 = time.time()
        print('知识边界判断', t3 - t2)

        try:
            # url = 'http://13.56.82.62:7000/mult_agent'
            if person.big5:
                big5 = json.loads(person.big5)
            else:
                big5 = []

            # body = {"mbti":person.mbti,
            #         "query":query,
            #         "history_str": history_str,
            #         "description":person.description,
            #         "habbit":person.habbit,
            #         "values_deal":person.values_deal,
            #         "big5":big5,
            #         'knowledge_flag':flag
            #         }
            # print('mult_agent入参',body)
            # response = requests.post(url=url,json=body)
            result = Role_play(MBTI=person.mbti, query={'query': query, 'history': history_str},
                               Profile=person.description, Topic_prefer=person.habbit, Values=person.values_deal,
                               Flag=1, Big5=big5)
            # t4 = time.time()
            # print('mult_agent时间',t4-t3)
            #
            # result = response.text

            result = json.loads(result)
            print('mult_agent的结果', result)
            return {"answer": result['data']}, 200
        except Exception as e:
            print(e)
            return {'message': "mult_agent报错" + result}, 400
        # appid =
        # query =
        # global agent_dict
        # if user in agent_dict.keys():
        #
        #     result = Role_play(Agents_list,query)
        #     return {'answer':result}


"""
{
  "big5": [
    "Visionary", "Naturalistic Intelligence", "Openness"
  ],
  "description": "",
  "habbit": "",
  "history_str": "",
  "knowledge_flag": 1,
  "mbti": "INTP",
  "query": "Who's your favourite teacher?",
  "values_deal": ""
}
"""


def t():
    time.sleep(2)
    print('test')
    return "success"


class Multi_agent(AppApiResource):
    def post(self, app_model: App):
        """
        Simulate a multi-agent conversation based on provided parameters
        ---
        tags:
          - restful
        parameters:
          - in: body
            name: app_model
            required: true
            description: A JSON object containing the conversation details
            schema:
              type: object
              properties:
                mbti:
                  type: string
                  description: The MBTI personality type of the person
                query:
                  type: string
                  description: The query or statement to be processed by the agents
                history_str:
                  type: string
                  description: Conversation history as a single string
                description:
                  type: string
                  description: A description of the person
                habbit:
                  type: string
                  description: The person's habits or preferences
                values_deal:
                  type: string
                  description: Processed values data
                big5:
                  type: array
                  description: Big Five personality traits
                  items:
                    type: string
                knowledge_flag:
                  type: integer
                  description: Flag indicating knowledge boundaries (1 for within limits, 0 for outside)
        responses:
          200:
            description: The result of the multi-agent simulation
            schema:
              type: object
              properties:
                code:
                  type: integer
                  description: Status code (0 for success)
                data:
                  type: string
                  description: The generated response from the agents
        """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('mbti', type=str, required=True, location='json', default=None)
            parser.add_argument('query', type=str, required=True, location='json', default=None)
            parser.add_argument('history_str', type=str, required=True, location='json', default=None)
            parser.add_argument('description', type=str, required=True, location='json', default=None)
            parser.add_argument('habbit', required=True, location='json', default=None)
            parser.add_argument('values_deal', required=True, location='json', default=None)
            parser.add_argument('big5', type=list, required=True, location='json', default=None)
            parser.add_argument('knowledge_flag', type=int, required=True, location='json', default=None)
            args = parser.parse_args()
            mbti = args['mbti']
            query = args['query']
            history_str = args['history_str']
            description = args['description']
            habbit = args['habbit']
            values_deal = args['values_deal']
            big5 = args['big5']
            knowledge_flag = args['knowledge_flag']
            # executor = ProcessPoolExecutor(max_workers=7)
            # p = executor.submit(t)
            # print(p.result())
            # print("before")
            # logger.info("hello world")
            # agentscope.init(
            #     # model_configs=os.path.join(os.path.dirname(os.path.abspath(__file__)), "./configs/Models_configs.json"),
            #     model_configs="./configs/Models_configs.json",
            #     logger_level="DEBUG")
            # logger.info("init finish")
            result = Role_play(Big5=big5,MBTI=mbti, query={'query': query, 'history': history_str}, Profile=description,
                       Topic_prefer=habbit, Values=values_deal, Flag=knowledge_flag)
            return {'code': 0, 'result': result}, 200
        except Exception as e:
            print(traceback.format_exc())
            raise


class Knowledge_limit(AppApiResource):
    def post(self, app_model: App):
        """
            Evaluate if a query is within the knowledge boundaries
            ---
            tags:
              - restful
            parameters:
              - in: body
                name: query
                required: false
                description: The query to be evaluated
                schema:
                  type: string
              - in: body
                name: knowledge_path
                required: false
                description: The knowledge path against which the query is evaluated
                schema:
                  type: array
                  items:
                    type: string
            responses:
              200:
                description: The result of the evaluation including the flag indicating if the query is within limits
                schema:
                  type: object
                  properties:
                    flag:
                      type: integer
                      description: 1 if within knowledge limits, 0 otherwise
            """
        parser = reqparse.RequestParser()
        parser.add_argument('query', type=str, required=False, location='json', default=None)
        parser.add_argument('knowledge_path', type=list, required=False, location='json', default=[])
        args = parser.parse_args()
        query = args['query']
        knowledge_path = args['knowledge_path']
        t0 = time.time()
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
        return result, 200


class knowledge_deal(AppApiResource):
    def post(self, app_model: App):
        """
        Process knowledge data and generate a knowledge path
        ---
        tags:
          - restful
        parameters:
          - in: body
            name: knowledge
            required: false
            description: The knowledge data to be processed
            schema:
              type: object
              properties:
                knowledge:
                  type: string
                  description: Knowledge content to be processed
        responses:
          200:
            description: The generated knowledge path
            schema:
              type: object
              properties:
                code:
                  type: integer
                  description: Status code (0 for success)
                data:
                  type: string
                  description: The processed knowledge path
        """
        parser = reqparse.RequestParser()
        parser.add_argument('knowledge', type=str, required=False, location='json', default='')
        args = parser.parse_args()
        knowledge = args['knowledge']
        knowedge_path = create_knowledge_path(knowledge)
        return {'code': 0, 'data': knowedge_path}, 200


api.add_resource(Create_model_person, '/create_model_person')
api.add_resource(Mult_agent_talk, '/multi_agent_talk')
api.add_resource(Multi_agent, '/multi_agent')
api.add_resource(Knowledge_limit, '/knowledge_limit')
api.add_resource(knowledge_deal, '/knowledge_deal')

# if __name__ == '__main__':
#     a = ModelPerson()
#     a.id = str(uuid.uuid4())
#     a.mbti = str(['s','fggf'])
#
#     db.session.add(a)
