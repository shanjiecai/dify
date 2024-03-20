import os

from openai.types.chat import ChatCompletion, ChatCompletionChunk

api_key = os.environ.get('OPENAI_API_KEY')
from openai import OpenAI, Stream

client = OpenAI(api_key=api_key)


# from flask import current_app
#
# api_key = current_app.config['OPENAI_API_KEY']
# openai.api_key = api_key


# def get_openai_api_key():
#     return api_key


def generate_response(prompt=None, system_prompt=None, history_messages=None, model="gpt-3.5-turbo", json_format=False,
                      **kwargs) -> ChatCompletion | Stream[ChatCompletionChunk]:
    if not prompt and not history_messages:
        raise ValueError("prompt and history_messages cannot be both empty.")
    if not prompt:
        messages = []
    else:
        messages = [
            {"role": "user", "content": prompt},
        ]
    if history_messages:
        messages.extend(history_messages)
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})
    # print(messages)
    response = client.chat.completions.create(model=model,
                                              max_tokens=kwargs.get('max_tokens', 100),
                                              temperature=kwargs.get('temperature', 0.7),
                                              presence_penalty=kwargs.get('presence_penalty', 0),
                                              frequency_penalty=kwargs.get('frequency_penalty', 0),
                                              top_p=kwargs.get('top_p', 1),
                                              stop=kwargs.get('stop', None),
                                              messages=messages,
                                              stream=kwargs.get('stream', False),
                                              response_format={"type": "json_object"} if json_format else {"type": "text"},
                                              timeout=kwargs.get('timeout', 120),
                                              )

    return response


if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    response = generate_response("", prompt)
    print(response)
