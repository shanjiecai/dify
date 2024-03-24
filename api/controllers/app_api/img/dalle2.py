

from controllers.app_api.openai_base_request import client


def dalle2_invoke(prompt, size="medium", n=1):

    SIZE_MAPPING = {
        'small': '256x256',
        'medium': '512x512',
        'large': '1024x1024',
    }


    # get size
    size = SIZE_MAPPING[size]


    # call openapi dalle2
    response = client.images.generate(
        prompt=prompt,
        model='dall-e-2',
        size=size,
        n=n,
        # response_format='url',
        response_format='b64_json',
    )

    result = []
    for image in response.data:
        # print(image.b64_json)
        result.append(image.b64_json)
    return result


if __name__ == '__main__':
    # test
    # print(dalle2_invoke("A futuristic robot typing on a keyboard with Python code projected in holographic displays around it, symbolizing the automation achieved through Python programming."))
    print(dalle2_invoke("A colorful digital illustration of a python coiling around a laptop displaying Python code on its screen, set against a backdrop of binary code."))

