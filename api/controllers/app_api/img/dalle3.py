from base64 import b64decode
import os
from os.path import join
from typing import Any, Union

from controllers.app_api.openai_base_request import client


def dalle3_invoke(prompt, size="vertical", n=1, quality="standard", style="vivid"):
    SIZE_MAPPING = {
        'square': '1024x1024',
        'vertical': '1024x1792',
        'horizontal': '1792x1024',
    }

    # get size
    size = SIZE_MAPPING[size]

    # call openapi dalle3
    response = client.images.generate(
        prompt=prompt,
        model='dall-e-3',
        size=size,
        n=n,
        quality=quality,
        style=style,
        # response_format='url',
        response_format='b64_json',
    )

    result = []
    for image in response.data:
        result.append(image.b64_json)
    return result


if __name__ == '__main__':
    # test
    print(dalle3_invoke(
        "A colorful digital illustration of a python coiling around a laptop displaying Python code on its screen, set against a backdrop of binary code."))
