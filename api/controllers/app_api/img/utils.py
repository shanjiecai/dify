import os
import random
import time
from base64 import b64decode
from typing import Union

import requests
from flask import Flask

from controllers.app_api.app.utils import upload_file
from controllers.app_api.openai_base_request import generate_dalle_query_variations_gpt
from models.model import Conversation
from mylogger import logger


def download_img_form_url(url, filepath):
    try:
        response = requests.get(url)
        file = open(filepath, "wb")
        file.write(response.content)
        file.close()
        return filepath
    except Exception as e:
        print(e)
        return None


def save_base64_img(base64_str, filepath):
    try:
        imgdata = b64decode(base64_str)
        with open(filepath, 'wb') as f:
            f.write(imgdata)
        return filepath
    except Exception as e:
        print(e)
        return None


def generate_img_pipeline(plan, model="dalle3", conversation: Conversation = None, main_app: Flask = None, **kwargs):
    def main():
        begin = time.time()
        perfect_prompt = generate_dalle_query_variations_gpt(plan)
        logger.info(f"生成图片pipeline耗时：{time.time() - begin}")
        # 取出所有v
        perfect_prompt_list = [v for k, v in perfect_prompt.items()]
        prompt = random.choice(perfect_prompt_list)
        if model == "dalle3":
            from controllers.app_api.img.dalle3 import dalle3_invoke
            img_list = dalle3_invoke(prompt, **kwargs)
        elif model == "cogview3":
            from controllers.app_api.img.cogview3 import cogview3_invoke
            img_list = cogview3_invoke(prompt, **kwargs)
        elif model == "dalle2":
            from controllers.app_api.img.dalle2 import dalle2_invoke
            img_list = dalle2_invoke(prompt, **kwargs)
        else:
            return None
        logger.info(f"生成图片pipeline耗时：{time.time() - begin}")
        images = []
        if img_list:
            for img in img_list:
                # image_name = url.split("/")[-1]
                image_name = f"{time.time()}.png"
                dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images", image_name)
                # download_img_form_url(img, dst)
                save_base64_img(img, dst)
                logger.info(f"下载图片耗时：{time.time() - begin}")
                res = upload_file(dst, image_name)
                logger.info(f"上传图片：{res}")
                """{
                    "data": {
                        "uuid": "e5b53831-fa5f-477c-bf7c-2e42d9ff67ff"
                    }
                }"""
                images.append({
                    "uuid": res["data"]["uuid"],
                    # "img": img
                })
        logger.info(f"生成图片pipeline耗时：{time.time() - begin}")
        return images, perfect_prompt_list
    if main_app:
        with main_app.app_context():
            images, perfect_prompt_list = main()
    else:
        images, perfect_prompt_list = main()
    return images, perfect_prompt_list


if __name__ == '__main__':
    # test
    print(generate_img_pipeline("python programming", model="dalle2"))
