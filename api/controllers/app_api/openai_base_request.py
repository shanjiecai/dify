import json
import os

import numpy as np
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from core.prompt_const import generate_dalle_query_template

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


def generate_dalle_query_variations_gpt(original_prompt, n_variations=1) -> dict[str, str]:
    print("Enriching prompt")
    template = generate_dalle_query_template.format(original_prompt=original_prompt, n_variations=n_variations)
    # generate variations of the prompt using the OpenAI API GPT 4
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=200,
        temperature=1.0,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that can generate creative variations of prompts for image "
                           "generation using stable diffusion. Remember to not violate any content policy "
                           "restrictions. Dont generate harmful, bad content",
            },
            {"role": "assistant", "content": f"{template}"},
        ],
        response_format={"type": "json_object"},
    )
    # parse the response and convert to dict

    query_variations = response.choices[0].message.content

    query_variations = json.loads(query_variations)

    return query_variations


def generate_embedding(prompt: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=prompt
    )

    return response.data[0].embedding


def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    return dot_product / (norm_a * norm_b)


def compare_similarity(prompt, tag_list=None):
    if tag_list is None:
        tag_list = ["Music", "Sports", "Art", "Games", "Gastronomy", "Tourism", "Religion"]
    prompt_embedding = generate_embedding(prompt)
    similarities = []
    # 同文件夹下tag_cache.json文件存在
    tag_cache_path = os.path.join(os.path.dirname(__file__), "tag_cache.json")
    if os.path.exists(tag_cache_path):
        with open(tag_cache_path) as f:
            tag_cache = json.load(f)
        for tag in tag_list:
            if tag in tag_cache:
                tag_embedding = tag_cache[tag]
            else:
                tag_embedding = generate_embedding(tag)
                tag_cache[tag] = tag_embedding
            similarity = cosine_similarity(prompt_embedding, tag_embedding)
            similarities.append(similarity)
    else:
        for tag in tag_list:
            tag_embedding = generate_embedding(tag)
            similarity = cosine_similarity(prompt_embedding, tag_embedding)
            similarities.append(similarity)
    # 返回所有相似度超过0.2的，如果没有返回最大
    similar_tag = [tag_list[i] for i in range(len(tag_list)) if similarities[i] > 0.2]
    if not similar_tag:
        similar_tag = [tag_list[similarities.index(max(similarities))]]
    return similar_tag


if __name__ == "__main__":
    # prompt = "What is the meaning of life?"
    # response = generate_response("", prompt)
    # print(response)
    print(generate_dalle_query_variations_gpt("python programming"))
    prompt = """A futuristic robot typing on a keyboard with Python code projected in holographic displays around it, 
    symbolizing the automation achieved through Python programming."""
    # from controllers.app_api.img.dalle2 import dalle2_invoke
    # print(dalle2_invoke(prompt))
    # print(generate_embedding(prompt))
    # tag_list = ["Music", "Sports", "Art", "Games", "Gastronomy", "Tourism", "Religion"]
    # with open("tag_cache.json", "w") as f:
    #     embedding = {}
    #     for tag in tag_list:
    #         embedding[tag] = generate_embedding(tag)
    #     json.dump(embedding, f)
    # print(compare_similarity("lose weight", ["Music", "Sports", "Art", "Games", "Gastronomy", "Tourism", "Religion"]))


