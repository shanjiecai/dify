from zhipuai import ZhipuAI

client = ZhipuAI(api_key="")  # 请填写您自己的APIKey

response = client.images.generations(
    model="cogview-3",  # 填写需要调用的模型名称
    prompt="一只可爱的小猫咪",
)
print(response.data[0].url)
