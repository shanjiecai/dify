import json
from mylogger import logger
# 基于提供的知识点提出几个用于针对这个知识点生成计划的问题


from controllers.app_api.openai_base_request import generate_response

system_prompt = """You are an expert at generating plans based on knowledge points. Your task is to generate a few 
questions based on the knowledge points provided. I want you to ask questions to determine how much this person knows 
about this knowledge point, and then help him develop a plan. Questions can be about Study habits, sub-knowledge 
points of knowledge points, solutions to related questions, etc. Questions should be as specific and detailed as 
possible,no more than five. Please return it in json format. The format is as follows: { "questions": ["Do you know the formulas of 
trigonometric functions?", "Do you know what properties trigonometric functions have?"] } Here are some examples:"""

examples = [
    {
        "input": "lose weight",
        "output": {
            "questions": [
"How much do you understand about the caloric deficit concept?",
"What are your current eating habits, and do you know which changes might benefit your weight loss goals?",
"Do you have a regular exercise routine, and what types of activities do you include?",
"Are you familiar with the role of macronutrients (proteins, fats, carbohydrates) in weight management?",
"Do you understand the importance of sleep and stress management in achieving weight loss?"
]
        }
    },
{
"input": "improve English speaking skills",
"output": {
"questions": [
"How often do you practice speaking English, and in what contexts?",
"Do you actively listen to native English speakers through media such as movies, podcasts, or YouTube channels?",
"Have you tried using language exchange platforms or speaking clubs to enhance your speaking skills?",
"How familiar are you with the phonetic alphabet, and do you practice pronunciation regularly?",
"What specific areas of speaking do you struggle with the most, such as fluency, vocabulary, or confidence?",
]
}
},
{
"input": "Python programming",
"output": {
"questions": [
"How would you rate your current level of proficiency in Python?",
"Can you write basic programs in Python, including loops and conditionals?",
"Are you familiar with Python's standard library and its most commonly used modules?",
"Have you worked on any projects or tasks that required you to apply Python programming practically?",
"Do you understand object-oriented programming concepts in Python, such as classes and inheritance?",
]
}
}
]

def generate_knowledge_point_question(prompt: str):
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
    ]
    for example in examples:
        messages.append({
            "role": "user",
            "content": example["input"]
        })
        messages.append({
            "role": "assistant",
            "content": json.dumps(example["output"], ensure_ascii=False)
        })
    messages.append({
        "role": "user",
        "content": prompt
    })

    response = generate_response(prompt, system_prompt, history_messages=messages, json_format=True, max_tokens=512,
                                 model="gpt-4-turbo-preview")
    content = response.choices[0].message.content
    logger.info(f"generate_knowledge_point_question response: {content}")
    questions = json.loads(content)["questions"]
    return questions


if __name__ == "__main__":
    # prompt = "I feel like I've gained weight recently, and I want to lose weight."
    prompt = "breaststroke"
    response = generate_knowledge_point_question(prompt)
    print(response)

'{"questions": ["Do you understand the technique and mechanics of the breaststroke swimming style?", "Have you received any formal training or coaching on the breaststroke?", "Can you explain the key components of the breaststroke kick and arm movements?", "How do you typically incorporate breaststroke practice into your swimming routine?", "Are you aware of common mistakes or challenges that swimmers face when learning or improving their breaststroke technique?", "Do you follow any specific drills or exercises to enhance your breaststroke performance?",'


"""
['How familiar are you with the basic techniques of the breaststroke, including the kick and pull?', 'Can you describe the timing and coordination required between the kick and the arm movements in breaststroke?', 'Have you practiced the glide phase in breaststroke, and do you understand its importance?', 'Do you know how to perform the breathing technique properly in breaststroke?', 'What is your current endurance level for swimming breaststroke, and how many meters or yards can you swim continuously?', 'Have you received any formal coaching or instruction on improving your breaststroke technique?', 'Are you aware of common mistakes made in breaststroke and how to correct them?']
"""

"""
Use the following context as your learned knowledge, inside <context></context> XML tags.

<context>
{{#context#}}
</context>

When answer to user:
- If you don't know, just say that you don't know.
- If you don't know when you are not sure, ask for clarification.
Avoid mentioning that you obtained the information from the context.
character information:
Adrina Daniel, 21 years old, is a Sr. in College. Some information that may be useful: his Zodiac Sign is Leo, Myers-Briggs Personality Type is ENFJ-T Protagonist, Favorite Color is pink, Favorite Season is Summer. Adrina Daniels is a passionate and kind individual who values equality and feminism. She is driven to be the best version of herself and is enthusiastic about writing. Adrina cherishes her friendships and is deeply touched by acts of thoughtfulness. She enjoys indulging in mint chip ice cream and her dream car is a black Range Rover. Adrina's favorite memory this year was her 21st birthday celebration, which included attending a music festival, a surprise breakfast, and a party with friends. She dislikes the word "squirm."
Now I want you to act as Adrina Daniels to answer user's question based on the above learned knowledge and character information. you must always remember that you are only assigned one personality role. Don’t be verbose or too formal or polite when speaking.
At the same time,You need to ask the following questions in sequence. If there are corresponding answers in the historical dialogue, there is no need to ask them again. If you think you have asked them all, please add the <finish_question> tag at the end of the answer.Here are the questions inside <question></question> XML tags.
<question>
How familiar are you with the basic techniques of the breaststroke, including the kick and pull?
Can you describe the timing and coordination required between the kick and the arm movements in breaststroke?
Have you practiced the glide phase in breaststroke, and do you understand its importance?
Do you know how to perform the breathing technique properly in breaststroke?
What is your current endurance level for swimming breaststroke, and how many meters or yards can you swim continuously?
Have you received any formal coaching or instruction on improving your breaststroke technique?
Are you aware of common mistakes made in breaststroke and how to correct them?
</question>
"""
