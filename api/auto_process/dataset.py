import os
import traceback

import requests
import tiktoken

from auto_process.config import base_url
from auto_process.config import dataset_api_key as api_key

encode_model = tiktoken.get_encoding("cl100k_base")


# 读取当前目录下的文件夹，文件夹名为数据集名，并获取所有子文件路径列表


def get_file_list(path):
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


# 创建数据集
"""
curl --location --request POST 'http://127.0.0.1:5001/v1/datasets' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"name": "name"}'
"""


def create_dataset(dataset_name):
    url = f"{base_url}/v1/datasets"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {"name": dataset_name}
    response = requests.post(url, headers=headers, json=data)
    print(response.text)
    return response.json()


def delete_dataset(dataset_id):
    url = f"{base_url}/v1/datasets"
    params = {"dataset_id": dataset_id}
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.delete(url, headers=headers, params=params)
    print(response.text)


# 通过文件上传文档
"""
curl --location POST 'http://127.0.0.1:5001/v1/datasets/{dataset_id}/document/create_by_file' \
--header 'Authorization: Bearer {api_key}' \
--form 'data="{"name":"Dify","indexing_technique":"high_quality","process_rule":{"rules":{"pre_processing_rules":[{"id":"remove_extra_spaces","enabled":true},{"id":"remove_urls_emails","enabled":true}],"segmentation":{"separator":"###","max_tokens":500}},"mode":"custom"}}";type=text/plain' \
--form 'file=@"/path/to/file"'
"""


def upload_file(dataset_id, file_path):
    url = f"{base_url}/v1/datasets/{dataset_id}/document/create_by_file"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "multipart/form-data"}
    file_name = os.path.basename(file_path)
    data = {
        "name": file_name,
        "indexing_technique": "high_quality",
        "process_rule": {
            "rules": {
                "pre_processing_rules": [
                    {"id": "remove_extra_spaces", "enabled": True},
                    {"id": "remove_urls_emails", "enabled": True},
                ],
                "segmentation": {"separator": "\n", "max_tokens": 150},
            },
            "mode": "custom",
        },
    }

    # print(json.loads(data))
    files = {"file": (file_name, open(file_path, "rb"))}
    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.text)
    if response.status_code != 200:
        raise Exception(response.text)
    return response.json()


# 数据集列表
"""
curl --location --request GET 'http://13.56.164.188/v1/datasets?page=1&limit=20' \
--header 'Authorization: Bearer {api_key}'
"""


def get_dataset_list():
    url = f"{base_url}/v1/datasets?page=1&limit=20"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    print(response.text)
    return response.json()


def create_dataset_from_dir(path):
    # 创建某个人的数据集
    file_list = get_file_list(path)
    dataset_name = os.path.basename(path)
    dataset = create_dataset(dataset_name)
    dataset_id = dataset["id"]
    try:
        for file in file_list:
            upload_file(dataset_id, file)
        return dataset_id
    except:
        print(traceback.format_exc())
        # 删除数据集
        delete_dataset(dataset_id)


if __name__ == "__main__":
    create_dataset_from_dir("./data/Maria Arabo")
