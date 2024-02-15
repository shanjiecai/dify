import os

from openai.types.chat import ChatCompletion

api_key = os.environ.get('OPENAI_API_KEY')
from openai import OpenAI
client = OpenAI(api_key=api_key)


# from flask import current_app
#
# api_key = current_app.config['OPENAI_API_KEY']
# openai.api_key = api_key


# def get_openai_api_key():
#     return api_key


def generate_response(prompt, system_prompt=None, model="gpt-3.5-turbo-0125", **kwargs) -> ChatCompletion:
    messages = [
        {"role": "user", "content": prompt},
    ]
    if system_prompt:
        messages.insert(0, {"role": "assistant", "content": system_prompt})

    response = client.chat.completions.create(model=model,
    max_tokens=kwargs.get('max_tokens', 100),
    temperature=kwargs.get('temperature', 0.7),
    presence_penalty=kwargs.get('presence_penalty', 0),
    frequency_penalty=kwargs.get('frequency_penalty', 0),
    top_p=kwargs.get('top_p', 1),
    stop=kwargs.get('stop', None),
    messages=messages,
    stream=False)

    return response


if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    response = generate_response("", prompt)
    print(response)