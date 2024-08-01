import json
import time
import uuid
from datetime import datetime

import requests
from flask_restful import reqparse

from controllers.app_api import api

# from controllers.app_api.mult_agent.mult_agent import *
from controllers.app_api.mult_agent.knowledge_limit import create_knowledge_path
from controllers.app_api.wraps import AppApiResource
from extensions.ext_database import db
from models.model import App, ModelPerson


class create_model_person(AppApiResource):

    def extract_info_with_gemini(self,values):

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


    def post(self,app_model: App):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=False, location='json',default=None)
        parser.add_argument('habbit', type=str, required=False, location='json',default=None)
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
                values_deal = self.extract_info_with_gemini(values)
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
        if appid :
            model_person = db.session.query(ModelPerson).filter(ModelPerson.appid == appid).first()
            if name:model_person.name = name
            if habbit:model_person.habbit = habbit
            if values:model_person.values = json.dumps(values)
            if values_deal:model_person.values_deal = values_deal
            if knowledge:model_person.knowledge = knowledge
            if mbti:model_person.mbti = mbti
            if audio_model_g_path:model_person.audio_model_g_path = audio_model_g_path
            if audio_model_s_path:model_person.audio_model_s_path = audio_model_s_path
            if audio_reference_path:model_person.audio_reference_path = audio_reference_path
            if audio_reference_text:model_person.audio_reference_text = audio_reference_text
            if description:model_person.description = description
            model_person.update_time = datetime.now()
            if big5:model_person.big5 = json.dumps(big5)
            if knowledge_path:model_person.knowledge_path = knowledge_path
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
            model_person.knowledge_path=knowledge_path
            db.session.add(model_person)
            db.session.commit()

            return {'appid':model_person.appid},200


class mult_agent_talk(AppApiResource):
    def post(self,app_model: App):
        t1 = time.time()
        parser = reqparse.RequestParser()
        parser.add_argument('appid', type=str, required=False, location='json',default = None)
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
            return {'message':"appid不对"},400
        print(person.name,person.id,person.mbti,person.knowledge)
        t2 = time.time()
        print('读取数据库时间',t2-t1)
        try:
            url = 'http://13.56.82.62:7000/knowledge_limit'
            body = {"query": query,
                    "knowledge_path": json.loads(person.knowledge_path),
                    }
            print('知识边界入参',body)
            response = requests.post(url=url, json=body)

            decision = response.json()
            flag =decision['flag']
        except Exception as e:
            print(e)
            # return {'message': "知识边界报错" +e}, 400
            flag = 1

        print(flag)
        t3 = time.time()
        print('知识边界判断',t3-t2)

        try:
            url = 'http://13.56.82.62:7000/mult_agent'
            if person.big5: big5 = json.loads(person.big5)
            else:big5 = []


            body = {"mbti":person.mbti,
                    "query":query,
                    "history_str": history_str,
                    "description":person.description,
                    "habbit":person.habbit,
                    "values_deal":person.values_deal,
                    "big5":big5,
                    'knowledge_flag':flag
                    }
            print('mult_agent入参',body)
            response = requests.post(url=url,json=body)
            # result = Role_play(MBTI=person.mbti, query={'query':query,'history':history_str}, Profile=person.description, Topic_prefer=person.habbit, Values=person.values_deal, Flag=1)
            t4 = time.time()
            print('mult_agent时间',t4-t3)

            result = response.text

            result = json.loads(result)
            print('mult_agent的结果',result)
            return {"answer":result['data']},200
        except Exception as e:
            print(e)
            return  {'message':"mult_agent报错"+result},400
        # appid =
        # query =
        # global agent_dict
        # if user in agent_dict.keys():
        #
        #     result = Role_play(Agents_list,query)
        #     return {'answer':result}



api.add_resource(create_model_person, '/create_model_person')

api.add_resource(mult_agent_talk, '/mult_agent_talk')


# if __name__ == '__main__':
#     a = ModelPerson()
#     a.id = str(uuid.uuid4())
#     a.mbti = str(['s','fggf'])
#
#     db.session.add(a)