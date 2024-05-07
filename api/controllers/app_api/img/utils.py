import os
import random
import time
from base64 import b64decode

import requests
from flask import Flask

from controllers.app_api.app.utils import upload_file
from models.model import Conversation
from mylogger import logger
from services.openai_base_request_service import generate_dalle_query_variations_gpt


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


def generate_plan_img_pipeline(plan, model="dalle3", conversation: Conversation = None, main_app: Flask = None,
                               **kwargs):
    def main():
        begin = time.time()
        if model == "search_engine":
            from controllers.app_api.img.search_engine import search_engine_invoke
            dst_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images")
            img_list = search_engine_invoke(plan, dst_dir=dst_dir)
            images = []
            if img_list:
                for image_name in img_list:
                    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images", image_name)
                    res = upload_file(dst, image_name)
                    logger.info(f"上传图片：{res}")
                    images.append({
                        "uuid": res["data"]["uuid"],
                    })
            logger.info(f"生成图片pipeline耗时：{time.time() - begin}")
            return images, []
        perfect_prompt = generate_dalle_query_variations_gpt(plan)
        logger.info(f"生成图片pipeline耗时：{time.time() - begin}")
        # 取出所有v
        perfect_prompt_list = [v for k, v in perfect_prompt.items()]
        prompt = random.choice(perfect_prompt_list)
        logger.info(f"img prompt: {prompt}")
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


# shape可选：square, vertical, horizontal
# size a*b 例如：1024*1024
def generate_img_pipeline(query, model="dalle3", shape: str = None, size: str=None, main_app: Flask = None, **kwargs):
    if shape and shape not in ["square", "vertical", "horizontal"]:
        shape = None
    if size:
        size = size.split("*")
        if len(size) != 2:
            size = None
        else:
            try:
                size = [int(size[0]), int(size[1])]
            except:
                size = None
    def main():
        begin = time.time()
        if model == "search_engine":
            from controllers.app_api.img.search_engine import search_engine_invoke
            dst_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images")
            img_list = search_engine_invoke(query, shape=shape, size=size, dst_dir=dst_dir)
            images = []
            if img_list:
                # print(img_list)
                for image_name in img_list:
                    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images", image_name)
                    res = upload_file(dst, image_name)
                    logger.info(f"上传图片：{res}")
                    images.append({
                        "uuid": res["data"]["uuid"],
                    })

            logger.info(f"生成图片pipeline耗时：{time.time() - begin}")
            return images

        elif model == "dalle3":
            from controllers.app_api.img.dalle3 import dalle3_invoke
            img_list = dalle3_invoke(query, size=shape, **kwargs)
        elif model == "cogview3":
            from controllers.app_api.img.cogview3 import cogview3_invoke
            img_list = cogview3_invoke(query, **kwargs)

        elif model == "dalle2":
            from controllers.app_api.img.dalle2 import dalle2_invoke
            img_list = dalle2_invoke(query, **kwargs)
        else:
            return None
        logger.info(f"生成图片pipeline耗时：{time.time() - begin}")
        images = []
        if img_list:
            for img in img_list:
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
        return images

    if main_app:
        with main_app.app_context():
            images = main()
    else:
        images = main()
    return images


if __name__ == '__main__':
    # test
    # print(generate_plan_img_pipeline("python programming", model="search_engine"))
    # print(generate_plan_img_pipeline("lose weight", model="search_engine"))
    print(generate_img_pipeline("lose weight", model="search_engine"))
