import openai

# from flask import current_app
#
# api_key = current_app.config['OPENAI_API_KEY']
# openai.api_key = api_key


# def get_openai_api_key():
#     return api_key


def generate_response(api_key, prompt, system_prompt=None, **kwargs):
    openai.api_key = api_key
    messages = [
        {"role": "user", "content": prompt},
    ]
    if system_prompt:
        messages.insert(0, {"role": "assistant", "content": system_prompt})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        max_tokens=kwargs.get('max_tokens', 300),
        temperature=kwargs.get('temperature', 0.7),
        presence_penalty=kwargs.get('presence_penalty', 0),
        frequency_penalty=kwargs.get('frequency_penalty', 0),
        top_p=kwargs.get('top_p', 1),
        stop=kwargs.get('stop', None),
        messages=messages,
        stream=False
    )

    return response.to_dict()


if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    response = generate_response("", prompt)
    print(response)