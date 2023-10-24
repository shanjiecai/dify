import openai

from core.model_providers.models.llm.base import BaseLLM


def judge_llm_active(api_key: str, histories: str, assistant_name: str):
    if not api_key:
        return False
    openai.api_key = api_key
    prompt = f'''You are {assistant_name} in a group chat.
    Here is the group chat histories, inside <histories></histories> XML tags.
    <histories>
    {histories}
    </histories>
    You should determine whether to answer as {assistant_name}, just answer yes or no
    '''
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        max_tokens=1,
        temperature=0.1,
        presence_penalty=0,
        frequency_penalty=0,
        top_p=1,
        messages=messages,
        stream=False
    )
    return response["choices"][0]["message"]["content"].strip().lower().startswith("yes")
