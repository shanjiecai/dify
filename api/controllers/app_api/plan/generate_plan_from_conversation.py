import json

# from controllers.app_api.openai_base_request import generate_response
from core.prompt_const import (
    generate_plan_detail_system_prompt,
    generate_plan_introduction_system_prompt,
)
from mylogger import logger
from services.openai_base_request_service import generate_response

# system_prompt = """You are an expert of making plans, your task is to give a plan for the entire week based on a
# given goal or knowledge point, the plan should be as detailed as possible, please return it in json format in {{
# "day1":["plan1", "plan2", ....] , "day2":["plan1", plan2", ...] , ...}} goal or knowledge point： {user_goal}"""


# system_prompt = """Provide a detailed weekly plan based on a given goal or knowledge point and conversation history
# in JSON format. The plan should outline specific tasks and activities for each day of the week. Ensure that the plan
# is comprehensive and covers all relevant aspects related to the specified goal or knowledge point: {user_goal}.
#
# Please note that the plan should be flexible enough to accommodate various goals or knowledge points and should be
# detailed enough to provide actionable guidance for the entire week.
#
# The plan should be designed to effectively achieve the specified goal or cover the outlined knowledge point. Ensure
# that the tasks are clearly defined and provide a cohesive progression towards the desired outcome.Please structure
# the plan in the following JSON format: {{ "day1": ["plan1", "plan2", ...], "day2": ["plan1", "plan2", ...],
# ... }} Where "plan1", "plan2", etc. represent the detailed activities or tasks for each day."""


# system_prompt = """Create a detailed weekly plan based on the given goal or knowledge point and the conversation
# history. The plan should outline specific tasks and activities for each day of the week in JSON format. Ensure that
# the plan is comprehensive and covers all relevant aspects related to the specified goal or knowledge point: {user_goal}.
#
# Include specific, quantifiable tasks and activities for each day of the week, which should be designed with
# measurable outcomes to track progress and effectiveness as much as possible, ensuring a clear pathway toward
# achieving the goal or thoroughly understanding the knowledge point
#
# The tasks should be clearly defined and provide a cohesive progression towards the desired outcome. Please structure
# the plan in the following JSON format: {{ "day1": ["plan1", "plan2", ...], "day2": ["plan1", "plan2", ...],
# ... }} Where "plan1", "plan2", etc. represent the detailed activities or tasks for each day."""


# system_prompt = """Please provide a detailed weekly plan in JSON format, tailored to a specific goal or knowledge
# point: {user_goal}. The plan should include specific, quantifiable tasks and activities for each day of the week,
# ensuring a clear pathway toward achieving the goal or thoroughly understanding the knowledge point. The plan should
# be comprehensive, covering all relevant aspects and offering actionable steps. Each task should be designed with
# measurable outcomes to track progress and effectiveness. The JSON structure should follow the format: {{ "day1": [
# "task1 - metric", "task2 - metric", ...], "day2": ["task1 - metric", "task2 - metric", ...], ... }}, where each task
# is paired with a quantifiable metric to assess progress."""

# system_prompt = """Hello, AI Planning Pro! Your task is to create a detailed weekly plan based on a given goal or
# knowledge point: {user_goal} . The plan should be returned in JSON format with the following structure:
#
# ```json
# {
# "day1": ["plan1", "plan2", ...],
# "day2": ["plan1", "plan2", ...],
# ...
# }
# ```
#
# Remember to tailor the plan to the provided goal or knowledge point. Ensure that each day's plan is comprehensive and
# specific. Do not forget to use the user's goal or knowledge point in the plan."""


def generate_plan_from_conversation(history_str: str = "", plan: str = ""):
    # messages = [
    #     {
    #         "role": "system",
    #         "content": generate_plan_detail_system_prompt.format(user_goal=plan)
    #     },
    # ]
    # if history_str:
    #     messages.append({
    #         "role": "user",
    #         "content": history_str
    #     })
    system_prompt = generate_plan_detail_system_prompt.format(user_goal=plan, history=history_str)
    # logger.info(f"generate_plan_from_conversation messages: {system_prompt}")
    response = generate_response(
        prompt=None,
        system_prompt=system_prompt,
        history_messages=None,
        json_format=True,
        max_tokens=1536,
        model="gpt-4o",
        stream=True,
        temperature=0.7,
    )
    # stream response
    content = ""
    for item in response:
        if item.choices[0].delta.content:
            # print(item.choices[0].delta.content)
            content += item.choices[0].delta.content

    # content = response.choices[0].message.content
    logger.info(f"generate_plan_from_conversation response: {content}")
    plan = json.loads(content)
    # json结构不一定遵循规范，需要处理
    """{
      "week_plan": {
        "day1": ["""
    # 例如这种需要取week_plan的value
    # 如果结构体plan只有一个key且value不是list，取value
    if len(plan) == 1 and not isinstance(list(plan.values())[0], list):
        plan = list(plan.values())[0]
    return plan


def generate_plan_introduction(plan: str):
    messages = [
        {"role": "system", "content": generate_plan_introduction_system_prompt},
        {"role": "user", "content": plan},
    ]
    logger.info(f"generate_plan_introduction messages: {messages}")
    response = generate_response(
        prompt=None, history_messages=messages, max_tokens=200, model="gpt-3.5-turbo", stream=False
    )

    introduction = response.choices[0].message.content
    logger.info(f"generate_plan_introduction response: {introduction}")
    return introduction


if __name__ == "__main__":
    plan = "learn IELTS"
    print(generate_plan_from_conversation(plan=plan))
    pass
