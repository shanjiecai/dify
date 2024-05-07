# from controllers.app_api.openai_base_request import generate_response
from core.prompt_const import judge_plan_examples, judge_plan_system_prompt
from mylogger import logger
from services.openai_base_request_service import generate_response

# system_template = """You are an expert in helping people make plans, and your task is to determine whether or not the
# user's words are needed to help him make a plan. If it is, you need to extract a short goal or knowledge point that
# the user may have included in the sentence, and if not, you need to reply "no". You can only return the short goal or
# knowledge point, or no, if you don't know please return no. Here are a few examples:"""


# system_template = """Hello, your task is to act as a planning expert. When the user asks for help in making a plan,
# you should determine if their words are necessary for making the plan. If the user's words are needed,
# extract a short goal or knowledge point from their sentence. If not, reply with "no". Your response should be limited
# to the short goal or knowledge point, or "no" if you're unsure. Here are a few examples to guide you. Remember,
# your goal is to provide specific and concise information in response to the user's request."""
#
#
# examples = [
#     {
#         "input": "I need to improve my coding skills to get a better job.",
#         "output": "improve coding skills",
#     },
#     {
#         "input": "I like cats more than dogs.",
#         "output": "no",
#     },
#     {
#         "input": "I think trigonometric functions are difficult",
#         "output": "trigonometric functions",
#     },
#     {
#         "input": "I like cats more than dogs.",
#         "output": "no",
#     },
#     {
#         "input": "I'm planning to run a marathon, so I need a training schedule.",
#         "output": "marathon",
#     },
#     {
#         "input": "I think the new movie was overrated.",
#         "output": "no",
#     }
# ]


def judge_plan(prompt: str):
    messages = [
        {
            "role": "system",
            "content": judge_plan_system_prompt
        },
    ]
    for example in judge_plan_examples:
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
    response = generate_response(prompt=None, system_prompt=None, history_messages=messages, model="gpt-4-turbo-preview")
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
