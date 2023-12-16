
## /app_list
- 每一个app代表一个具体人物和模型
- 例如Adrina Daniel(4)表示Adrina Daniel这个人物，4表示使用的模型是gpt-4  
Alexa Caramazza表示Alexa Caramazza这个人物，没有数字表示使用的模型是gpt-3.5-turbo  
Adrina Daniel(chatglm)表示Adrina Daniel这个人物，chatglm表示使用的模型是chatglm-turbo  
- 返回格式  
```json
[
    {
        "name": "Adrina Daniel(4)",
        "id": "94aad33c-d817-4da7-917a-fc34df0dedfc",
        "model": "gpt-4"
    },
    {
        "name": "Alexa Caramazza",
        "id": "61a97d22-c636-4f4e-83a0-8704d3504b51",
        "model": "gpt-3.5-turbo"
    },
    {
        "name": "Adrina Daniel(chatglm)",
        "id": "cca4175d-339f-489d-921d-03c45033574c",
        "model": "chatglm-turbo"
    },
    ...
]
```

## /conversation
- 基于app_id新建conversation，用于模型多轮对话，超出长度目前的做法是截断最大轮数或基于之前的超长对话历史生成摘要
输入app_id
```
{
    "app_id":"ba0dd05e-c088-4cd0-b9ae-ddb55fcc5a46"
}
```

返回conversation_id
```
{
    "result": "success",
    "conversation_id": "5bda9554-1a09-4c22-82fe-44c454808f85"
}
```

- 之后群聊对话基于当前app_id和conversation_id进行，如果换新话题需要重新生成conversation_id  
- 需要实现基本的conversation表和message表
- conversation表主要字段  
```txt
id,app_id,created_at,updated_at,
model_name,model_config # 认为在一个conversation中不能切换模型，不能修改模型配置
```

- message表主要字段  
```txt
id,app_id,conversation_id,message,created_at,updated_at,  
role, # 当前消息的用户名
mood # 当前用户的情绪
```

- 需要根据当前对话的历史拼接模型的多轮输入，不同模型的拼接方式不同，因为是群聊多人聊天，可以按照如下形式组织prompt，也可以根据模型特性设计其他结构
```
user1:hello
user2:hi
user1:how are you
user2:fine
user3:what are you doing
user4:nothing
```

## /conversations/add_message
用于与app端同步单条信息需要在调用模型接口之前  

输入
```
{
    "message": "hi",
    "conversation_id": "a79f9b98-1576-4e7a-9808-0a1f92a63a74",
    "user":"hhd33",
    "app_id":"a756e5d2-c735-4f68-8db0-1de49333501c"
}
```
需要新建一个message关联conversation_id  

## /conversations//chat-messages-active

同步模型后调用模型接口，返回模型生成的回复  
因为是群聊模式需要先判断机器人是否应该插话，如果应该插话则返回机器人的回复，否则返回false  
- 1、判断机器人是否应该回话逻辑。   
当前没有专门微调模型，准确率不高，因此后面增加主动模块增加机器人活跃度，后续需要微调个小模型，用于判断机器人是否应该回话
```python
import openai
from mylogger import logger
import random
def judge_llm_active(api_key: str, histories: str, assistant_name: str, is_random_true: bool = True):
    if not api_key:
        return False
    openai.api_key = api_key
    if assistant_name != "James Corden":
        prompt = f'''You are {assistant_name} in a group chat.
        You need to participate in the group chat. Here is the group chat histories, inside <histories></histories> XML tags.
        <histories>
        {histories}
        </histories>
        You should determine whether to answer as {assistant_name}, just return yes or no
        '''
    else:
        # 主持人prompt，尽量活跃气氛
        prompt = f'''You are {assistant_name} or DJ Bot in a group chat.As the host of the group chat, you need to participate in the group chat and try to liven up the atmosphere.
        Here is the group chat histories, inside <histories></histories> XML tags.
        <histories>
        {histories}
        </histories>
        You should determine whether to answer as {assistant_name} or DJ Bot, just return yes or no
        '''
    logger.info(len(prompt))
    if len(prompt) > 10000:
        prompt = prompt[:10000]

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    # 调用模型接口
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        max_tokens=1,
        temperature=0,
        presence_penalty=0,
        frequency_penalty=0,
        top_p=1,
        messages=messages,
        stream=False
    )
    # 加入一定概率让能返回True
    if is_random_true and random.random() < 0.2:
        return True
    return response["choices"][0]["message"]["content"].strip().lower().startswith("yes")
history = get_history_from_triple()  # 从triples中获取历史
if judge_llm_active(api_key, history, assistant_name):
    # 调用模型接口
    completion(
        app_id=app_id,
        query=query, # 用户输入
        user_name="", # 用户名字
        assistant_name="", # 机器人名字
        conversation_id=conversation_id, 
        streaming=False,
        outer_memory=history,
    )
```
- 2、调用模型接口，app端不支持流式调用，需要将历史拼接到prompt中  

需要实现的函数
```python
response = completion(
    app_id=app_id,
    query=query, # 用户输入
    user_name="", # 用户名字
    assistant_name="", # 机器人名字
    conversation_id=conversation_id, 
    streaming=False,  # 是否流式调用
    outer_memory=None,  # 用于主动模块的外部记忆
)
```


## 获取当前app group chat的message，定期与客户端同步记录（还未实现）
比如每天定时同步一次，同步因为网络等问题导致的丢失的message









