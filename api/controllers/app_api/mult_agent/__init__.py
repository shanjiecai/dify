import uuid

from controllers.app_api.wraps import AppApiResource
from flask_restful import reqparse
from datetime import datetime
from models.model import ModelPerson, App
from extensions.ext_database import db
from controllers.app_api import api
import requests
import json


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
        parser.add_argument('name', type=str, required=False, location='json')
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

        if not values_deal:
            if values:
                values_deal = self.extract_info_with_gemini(values)
            else:
                values_deal = None
        model_person = ModelPerson()
        model_person.id = str(uuid.uuid4())
        model_person.name = name
        model_person.habbit = habbit
        model_person.values = str(values)
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
        db.session.add(model_person)
        db.session.commit()

        return {'appid':model_person.appid},200


class mult_agent_talk(AppApiResource):
    def post(self,app_model: App):
        parser = reqparse.RequestParser()
        parser.add_argument('appid', type=str, required=False, location='json',default = None)
        parser.add_argument('query', type=str, required=False, location='json', default=None)
        args = parser.parse_args()
        appid = args['appid']
        query = args['query']
        print(appid)
        person = db.session.query(ModelPerson).filter(ModelPerson.appid == appid).first()
        print(person)
        print(person.name,person.id,person.mbti,person.knowledge)

        return {}
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