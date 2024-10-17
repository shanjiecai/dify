# from controllers.app_api.openai_base_request import generate_response
from core.prompt_const import judge_force_plan_system_prompt, judge_plan_system_prompt
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
    messages = [{"role": "system", "content": judge_plan_system_prompt}, {"role": "user", "content": prompt}]
    # for example in judge_plan_examples:
    #     messages.append({
    #         "role": "user",
    #         "content": example["input"]
    #     })
    #     messages.append({
    #         "role": "assistant",
    #         "content": example["output"]
    #     })
    logger.info(f"judge_plan messages: {messages}")
    response = generate_response(
        prompt=None, system_prompt=None, history_messages=messages, model="gpt-4o", max_tokens=50
    )
    content = response.choices[0].message.content
    # logger.debug(f"judge_plan response: {content}")
    if "\n" in content:
        content = content.split("\n")[0]
    if "Assistant:" in content:
        content = content.split("Assistant:")[1]
    logger.debug(f"judge_plan response: {content}")
    return content


def judge_force_plan(prompt: str):
    messages = [
        {"role": "system", "content": judge_force_plan_system_prompt},
        {"role": "user", "content": prompt + "\nif the user's input contains explicit intent to create a plan?"},
    ]
    logger.info(f"judge_force_plan messages: {messages}")
    response = generate_response(
        prompt=None, system_prompt=None, history_messages=messages, model="gpt-4o", max_tokens=50
    )
    content = response.choices[0].message.content
    # logger.debug(f"judge_force_plan response: {content}")
    if "\n" in content:
        content = content.split("\n")[0]
    if "Assistant:" in content:
        content = content.split("Assistant:")[1]
    logger.debug(f"judge_force_plan response: {content}")
    return content


if __name__ == "__main__":
    # prompt = "I feel like I've gained weight recently, and I want to lose weight."
    # prompt = "Anyone here"
    # prompt = """
    # a:我最近好胖想减肥
    # b:dddd
    # c:rrrrr
    # b:fffff
    # """
    # prompt = "I don't understand trigonometric functions"
    # prompt = "I feel like I've gained weight recently and want to lose weight."
    # prompt = "I feel like I've gained weight recently and want to lose weight."
    # prompt = "I want to learn k8s recently, give me a week plan"
    # prompt = "Suggest a 5-step plan to develop a budget-friendly healthy meal."
    # prompt = "I find mathematics very interesting and I want to learn trigonometric functions"
    # prompt = "I want to make a plan to lose weight"
    # prompt = "You are such a nice person.Can you help me make a one week plan for math?"
    # prompt = "@Yyh 2707 hotmail(AI) Can you give me a plan for walking 15km in 10 days?"
    prompt = "learn football"
    # prompt = "Put together a business plan for a new restaurant."
    # prompt = "you are silly"
    response = judge_plan(prompt)
    # response = judge_force_plan(prompt)
    print(response)
