from controllers.app_api.openai_base_request import generate_response
from mylogger import logger

system_template = """You are an expert in helping people make plans, and your task is to determine whether or not the 
user's words are needed to help him make a plan. If it is, you need to extract a short goal or knowledge point that 
the user may have included in the sentence, and if not, you need to reply "no". You can only return target, 
knowledge or no, if you don't know please return no. Here are a few examples:"""

examples = [
    {
        "input": "I need to improve my coding skills to get a better job.",
        "output": "improve coding skills",
    },
    {
        "input": "I like cats more than dogs.",
        "output": "no",
    },
    {
        "input": "I think trigonometric functions are difficult",
        "output": "trigonometric functions",
    },
    {
        "input": "I like cats more than dogs.",
        "output": "no",
    },
    {
        "input": "I'm planning to run a marathon, so I need a training schedule.",
        "output": "marathon",
    },
    {
        "input": "I think the new movie was overrated.",
        "output": "no",
    }
]


def judge_plan(prompt: str):
    messages = [
        {
            "role": "system",
            "content": system_template
        },
    ]
    for example in examples:
        messages.append({
            "role": "user",
            "content": example["input"]
        })
        messages.append({
            "role": "assistant",
            "content": example["output"]
        })
    messages.append({
        "role": "user",
        "content": prompt
    })
    logger.info(f"judge_plan messages: {messages}")
    response = generate_response(prompt, system_template, history_messages=messages)
    content = response.choices[0].message.content
    logger.info(f"judge_plan response: {content}")
    return content


if __name__ == "__main__":
    # prompt = "I feel like I've gained weight recently, and I want to lose weight."
    # prompt = "Anyone here"
    prompt = """
    a:我最近好胖想减肥
    b:dddd
    c:rrrrr
    b:fffff
    """
    response = judge_plan(prompt)
    print(response)
