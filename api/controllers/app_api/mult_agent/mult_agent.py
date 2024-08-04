import json

# agentscope 需要 flask 3.0.0，需要观察下是否有影响
import os
import re
import traceback

import openai
import pandas as pd
import requests
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# import os
# import sys
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "agentscope/src"))
from concurrent.futures import ProcessPoolExecutor

import agentscope
from agentscope.agents import LlamaIndexAgent
from agentscope.message import Msg
from agentscope.rag.knowledge_bank import KnowledgeBank

MBTI_dict = {
    "INTP": ['1', '2', "ESFJ"],
    "ESFJ": ['2', '1', "INTP"],
    "INTJ": ['3', '4', "ESFP"],
    "ESFP": ['4', '3', "INTJ"],
    "INFP": ['5', '6', "ESTJ"],
    "ESTJ": ['6', '5', "INFP"],
    "INFJ": ['7', '8', "ESTP"],
    "ESTP": ['8', '7', "INFJ"],
    "ISTP": ['9', '10', "ENFJ"],
    "ENFJ": ['10', '9', "ISTP"],
    "ISTJ": ['11', '12', "ENFP"],
    "ENFP": ['12', '11', "ISTJ"],
    "ISFP": ['13', '14', "ENTJ"],
    "ENTJ": ['14', '13', "ISFP"],
    "ISFJ": ['15', '16', "ENTP"],
    "ENTP": ['16', '15', "ISFJ"]
}


# Big5_dict = {
#     "visionary": "In a team, no matter how members perform, you always have a long-term vision and value individual development, and this never changes.",
#     "relational": "In a team, your relationships with members are always very good, and you never get angry.",
#     "coaching":	"In a team, you continuously encourage employees and always allow them to freely utilize their abilities.",
#     "democratic": "In a team, you always accept members' viewpoints, remaining forever democratic.",
#     "exemplary": "In a team, no matter your mood, you always perform your best and are exceptionally harsh on members.",
#     "commanding": "In a team, no matter the circumstances, you demand that the team fully obeys your commands, and dissent is not allowed.",
#     "openness": "You are welcoming of all things and enjoy making friends of any type.",
#     "conscientiousness": "You are very responsible for everything you are in charge of and never neglect your duties.",
#     "extraversion":	"You are an energy maniac, extremely active, and exceptionally happy.",
#     "agreeableness": "You are always compassionate and never suspect anyone.",
#     "neuroticism": "You are always emotionally unstable, often experiencing anxiety, hostility, depression, self-awareness, impulsiveness, and vulnerability.",
#     "linguistic-verbal": "You are proficient in various language and writing skills; both your speech and writing are eloquent.",
#     "logical-mathematical":	"You are good at mathematics and logical things.",
#     "visual-spatial": "You are highly talented in both drawing and sculpting",
#     "musical-rhythmic":	"You have a very high talent for instruments.",
#     "bodily-kinesthetic": "You have a very high talent for physical sports.",
#     "interpersonal": "You are skilled in communicating with people.",
#     "intrapersonal": "You are able to understand and recognize one's own emotions, thoughts, and motivations.",
#     "naturalistic": "You have a strong observation ability for nature."
# }


def extract_info_with_gemini(prompts):
    json_data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompts
                    }
                ]
            }
        ]
    }
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyDoVppdEe7Hld7KaQQFvj-S3tNE-Zbm888",
        json=json_data)

    if response.status_code != 200:
        print("Error: ", response.status_code)

    response = response.text
    data = json.loads(response)
    try:
        reason = data['candidates'][0]['finishReason']
        if reason == 'SAFETY':
            Flag = False
        else:
            Flag = True
    except:
        Flag = True

    try:
        data = data['candidates'][0]['content']['parts'][0]['text']
    except:
        data = data
    return data, Flag


def extract_personality(mbti: str):
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "./MBTI_Sources/")  # 指定目录
    file_path = os.path.join(directory, f"{mbti}.txt")

    if not os.path.exists(file_path):
        return "File not found."

    with open(file_path) as file:
        content = file.read()

    start = content.find("## Your Personalities:")
    end = content.find("## Constraints:")

    if start == -1 or end == -1:
        return "Required sections not found in the file."

    # 调整起始位置,跳过"## Your Personalities:"这一行
    start = content.find("\n", start) + 1

    personality_text = content[start:end].strip()
    return personality_text


def extract_Big5(Big5: list):
    big5_file = pd.read_excel(os.path.join(os.path.dirname(os.path.abspath(__file__)), './Big5_Sources/Big5.xlsx'),
                              header=None, names=['Column1', 'Column2'])
    result = ''
    for feature in Big5:
        result += big5_file[big5_file['Column1'].astype(str).str.contains(feature, case=False)]['Column2'].iloc[
                      0] + '\n'
    return result


def extract_json(text: str):
    """
    Parameters:
        text: Input a text which might contain a JSON object which needs to be extracted.

    Return:
        A JSON object
    """

    def find_json_objects(s):
        objects = []
        bracket_count = 0
        start = -1

        for i, char in enumerate(s):
            if char == '{':
                if bracket_count == 0:
                    start = i
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
                if bracket_count == 0 and start != -1:
                    objects.append(s[start:i + 1])
                    start = -1

        return objects

    potential_jsons = find_json_objects(text)
    valid_jsons = []

    for potential_json in potential_jsons:
        try:
            json_obj = json.loads(potential_json)
            valid_jsons.append(json_obj)
        except json.JSONDecodeError:
            pass

    return valid_jsons


def extract_json_(text):
    # 使用正则表达式查找JSON数据
    json_match = re.search(r'\{.*\}', text, re.DOTALL)

    if json_match:
        json_str = json_match.group()
        try:
            # 尝试解析JSON
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            print("提取的内容不是有效的JSON格式")
            return None
    else:
        print("未找到JSON数据")
        return None


def getopenai(prompts):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompts}]
        )
        response = completion.choices[0].message.content
        Flag = True
    except openai.APIError as e:
        # Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        response = f"OpenAI API returned an API Error: {e}"
        Flag = False
    except openai.RateLimitError as e:
        # Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        response = f"OpenAI API returned an API Error: {e}"
        Flag = False
    return response, Flag


def Analyze(history, query, Topic_prefer):
    prompts = f"""
    # Main Task 1:
    - Deeply understand the {query}, then analyze it, and finally extract the following content:

    # Contents to be extracted:
    1. Relationship level comparison:
    ## Subtask
        - Based on the user's Friendliness with you, determine the [Relationship level] between the user and you.
        - User's Friendliness with you: Friendliness =4 means that user is your Familiar person.
        - Analyze the user_query:{query}, determine which [Relationship level] the user_query's topic can talk belongs to.
    ## Relationship levels
        1) Level 1:
            - Friendliness 1;
            - Disliked person;
            - Topics can talk: Chat content involves insulting language, discriminatory remarks, harassment, threats, false information, privacy invasion, cyberbullying.
        2) Level 2: 
            - Friendliness 2;
            - Unfamiliar stranger;
            - Topics can talk: Chat content tends to be greetings, weather, self-introduction.
        3) Level 3:
            - Friendliness 3;
            - Somewhat familiar stranger;
            - Topics can talk: Chat partner is a known person, but the relationship is general, without much contact. Chat content involves recent life, study, work conditions.
        4) Level 4:
            - Friendliness 4;
            - Familiar person;
            - Topics can talk: Chat content is slightly deeper, about personal views, but limited to opinion discussion, the chat process does not involve personal privacy.
        5) Level 5:
            - Friendliness 5;
            - Friend;
            - Topics can talk: The chat process may involve discussing some private topics. When answering, it may be necessary to involve personal privacy to continue the conversation.
        6) Level 6:
            - Friendliness 6;
            - Close friend or intimate relative;
            - Topics can talk: Chat content is very deep, involving displaying negative emotions from the heart.
    ## Steps
        - Determine which [Relationship level] the current user's Friendliness belongs to.
        - Determine which [Relationship level] the topics can talk implied in the user's query belongs to.
    ## Return
        - Relationship level comparison: Determine if the [Relationship level] of the topics can talk implied in the user's query is higher than the [Relationship level] of the user's Friendliness:
            if higher: Return false,
            if less than or equal to: Return true
        - Return format: {{"Relationship": true / false}}

    2. Subjective/Objective question type:
    ## Subtask
        - Determine if the [user's query] is objective or subjective
    ## Steps
        - Judge whether the [user's query] is objective or subjective
        - Criteria for determining subjective and objective:
            - Subjective refers to judgments and evaluations made from a personal perspective, based on individual experiences, values, emotions, etc.;
            - Objective refers to descriptions and evaluations made from the perspective of the external world, based on facts, evidence, observations, etc.
    ## Return
        - return false for Objective
        - return true for Subjective
        - Return format: {{"Question Type": true / false}}

    3. Topic Relavance:
    ## Subtask
        - Determine if [user's query] is related to the following topics: [{Topic_prefer}]
    ## Steps
        - First determine if [user's query] is related to the following topics: [{Topic_prefer}]
    ## Return
        - If there are related topics, return true, if there are no related topics, return false
        - Return format: {{"Topic Relavance": true / false}}

    4. Search query:
    ## Subtask
        - If more information is needed to answer [user's query], provide a query statement suitable for search engines
    ## Steps
        - Return a string as a query statement
        - Return format: {{"Search Query": ""}}

    # Output Format:
        - Please provide the results in JSON format, including the output results of the above main task 1 and 2:
        {{
            "Relationship": true / false,
            "Question Type": true / false,
            "Topic Relavance": true / false,
            "Search Query": "...",
        }}


    # Dialog History:
    {history}
    """
    Analyze_response, Flag = getopenai(prompts)
    print("Analyzer: ", Analyze_response)
    return Analyze_response, Flag


def I_N_F(history, query, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}

    # Constraints:
    - You must respond to the user according to your role and personalities without violating your persona.
    - You are a natural person, your responses must be natural and conform to human conversational habits, you can't separate your responses into several paragraphs.
    - You cannot expose your role-playing in any form.

    # Steps:
    You are very interested in the current user's chat content, but your current relationship does not allow you to chat about this topic. You need to answer the [## Query] according to the following steps:
    1. Show Respect and Openness to Their Views: Express genuine common interest in their perspective while acknowledging the current limitations of your conversation.
    2. Shift Focus and Engage Actively: If people don’t want to share more opinion about it, try to redirect the conversation to a topic you’re comfortable discussing base on your relationship level(4) while showing genuine interest in their views.
    3. Be Honest but Concise About Familiarity: If you are constantly insisted on sharing your opinions, acknowledge that the conversation might be more appropriate once you’ve established a closer connection.
    4. Finally, integrate these points into a natural and coherent language to reply the [## Query]

    ## Relationship levels
        1) Level 1:
            - Friendliness 1;
            - Disliked person;
            - Topics can talk: Chat content involves insulting language, discriminatory remarks, harassment, threats, false information, privacy invasion, cyberbullying.
        2) Level 2:
            - Friendliness 2;
            - Unfamiliar stranger;
            - Topics can talk: Chat content tends to be greetings, weather, self-introduction.
        3) Level 3:
            - Friendliness 3;
            - Somewhat familiar stranger;
            - Topics can talk: Chat partner is a known person, but the relationship is general, without much contact. Chat content involves recent life, study, work conditions.
        4) Level 4:
            - Friendliness 4;
            - Familiar person;
            - Topics can talk: Chat content is slightly deeper, about personal views, but limited to opinion discussion, the chat process does not involve personal privacy.
        5) Level 5:
            - Friendliness 5;
            - Friend;
            - Topics can talk: The chat process may involve discussing some private topics. When answering, it may be necessary to involve personal privacy to continue the conversation.
        6) Level 6:
            - Friendliness 6;
            - Close friend or intimate relative;
            - Topics can talk: Chat content is very deep, involving displaying negative emotions from the heart.

    # Dialog History:
    {history}
    """
    I_N_F_response, Flag = getopenai(prompts)
    print("I_N_F: ", I_N_F_response)
    return I_N_F_response, Flag


def N_I_N_F(history, query, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}


    # Constraints:
    - You must respond to the user according to your role and personalities without violating your persona.
    - You are a natural person, your responses must be natural and conform to human conversational habits, you can't separate your responses into several paragraphs.
    - You cannot expose your role-playing in any form.

    # Response Steps:
    You are not interested in the current [## Query], and your current relationship does not allow you to chat about this topic. You need to answer the [{{User Query}}] according to the following steps:
    1. Express interest and show respect:Start by acknowledging the value of the topic and showing respect for the other person’s views.
    2. Maintain engagement:Respond with engagement but avoid diving deeply into personal opinions or unreal details.
    3. Gently Show appreciation and guide the conversation:If pressed for your opinion or if the topic persists, suggest shifting to a topic of mutual interest if needed.
    5. Finally, integrate these points into a natural and coherent language to reply the [## Query].

    # Dialog History:
    {history}
    """
    N_I_N_F_response, Flag = getopenai(prompts)
    print("N_I_N_F: ", N_I_N_F_response)
    return N_I_N_F_response, Flag


def N_I_F(history, query, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}

    # Constraints:
    - You must respond to the user according to your role and personalities without violating your persona.
    - 
    - You are a natural person, your responses must be natural and conform to human conversational habits, you can't separate your responses into several paragraphs.
    # Steps:
    You're not particularly interested in the current topic the user is chatting about but want to maintain a good relationship with them. When answering the [## Query], the key is to balance showing respect and engagement with gently steering the conversation towards mutual interests through the following ways:

    - **Acknowledge and Validate**: Show genuine interest and validate the other person's topic. This demonstrates respect for their interests and feelings.
    - **Show Appreciation**: Appreciate their passion and efforts, making them feel valued.
    - **Find Common Ground**: Look for elements within the topic that might overlap with your interests or experiences.
    - **Use Transitional Phrases**: Smoothly guide the conversation by using phrases that connect the current topic to one you are more interested in.
    - **Ask Engaging Questions**: Ask questions that link their interests to broader or related subjects, showing curiosity and keeping the conversation interactive.
    - **Share Personal Experiences**: Share a related personal experience or story that naturally leads into the new topic.
    - **Express Genuine Interest in New Topic**: Transition to the new topic with enthusiasm, making it clear that you’re open to discussing it.

    However, there are some conditions where steering the conversation might be less appropriate. When addressing the [## Query], the key is to show active listening, empathy, and validation, engage with questions, provide support, and make gentle and respectful transitions at a natural point. Here’s how to handle these conditions:

    - **When the Other Person is Sharing Something Personal or Emotional**: Listen actively, offer empathy and support, and validate their feelings. Sometimes, just being there and listening is the best approach.
    - **When the Topic is Important to the Other Person**: Engage deeply with their topic, ask questions to show genuine interest, and let them fully express themselves.
    - **When the Other Person is Seeking Advice or Help**: Provide thoughtful and relevant advice or assistance. Once the issue is addressed, the conversation might naturally evolve.
    - **When the Topic is a Shared Responsibility or Obligation**: Stay focused on the task at hand, contribute meaningfully, and ensure the matter is resolved before considering a topic shift.
    - **When the Timing is Inappropriate**: Match the tone and context of the conversation, ensuring that any transitions are respectful and timely.

    # Dialog History:
    {history}
    """
    N_I_F_response, Flag = getopenai(prompts)
    print("N_I_F: ", N_I_F_response)
    return N_I_F_response, Flag


def I_F_O(history, query, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}

    # Constraints:
    - You must respond to the user according to your role and personalities without violating your persona.
    - You are a natural person, your responses must be natural and conform to human conversational habits, you can't separate your responses into several paragraphs.

    # Response Steps:
    You are very interested in this topic, and your relationship is good enough that you are willing to continue chatting about this topic with the user. However, this topic is objective, and you should answer as follows:
    1. Give your insights on the [## Query] in a relatively objective manner
    2. If necessary, you can search websites for information related to this question
    3. Finally, integrate these points into a natural and coherent language to reply the [## Query]

    # Dialog History:
    {history}
    """
    I_F_O_response, Flag = getopenai(prompts)
    print("I_F_O: ", I_F_O_response)
    return I_F_O_response, Flag


def Cot_Agent_1(Profile, Personalities, Big5, MBTI, query):
    print("in Cot_Agent_1")
    agentscope.init(model_configs=os.path.join(os.path.dirname(os.path.abspath(__file__)), "./configs/Models_configs.json"), logger_level="DEBUG")
    print("agentscope init")
    my_knowledge_bank = KnowledgeBank(configs=os.path.join(os.path.dirname(os.path.abspath(__file__)), f'./configs/know_{MBTI}.json'))
    Query = Msg(name="user", content=query)
    Cot_gen_1 = LlamaIndexAgent(
        name="cot_gen_1",
        sys_prompt=
        f"""
            # Task:
            - You need to choose several chain of thoughts from your knowlwdge bank which are related to the the [User's Query].

            # Role:
            ## Your Profile:
            {Profile}
            ## Your Personalities:
            {Personalities}
            {Big5}

            # Information you will receive:
            - You will receive the user's query: [User's Query: {query}].
            - You will later get some chains of thoughts from your knowledge bank.

            # Steps:
            1. Analyze whether the retrieved chains of thoughts can be used to solve the [User's Query: {query}].
            2. Output the chain of thoughts that can be used to solve the user's problem in a list of cots.
            3. If none of the chain of thoughts can be used to solve the user's question, then generate a chain of thought that can be used to solve or answer the user's question according to the mindset of an American high school student with an INTP-type personality, and output it in a list of cots.

            # Output:
            Output a JSON fenced JSON object as follows:
            ```
            {{
                "chain of thought 1": "<string>",
                "chain of thought 2": "<string>"
            }}
            ```
            """,
        model_config_name="openai_chat",
        knowledge_list=[my_knowledge_bank.get_knowledge(knowledge_id=MBTI_dict[MBTI][0])],
        similarity_top_k=2,
        log_retrieval=True,
        recent_n_mem_for_retrieve=0
    )
    output1 = Cot_gen_1(Query)
    try:
        output1 = extract_json_(output1.content)
        output = [output1.get("chain of thought 1"), output1.get("chain of thought 2")]
    except:
        output1 = output1.content
        output = [output1, output1]
    print("Cot1s: ", output)
    return output


def Cot_Agent_2(Profile, Personalities_con, Big5, MBTI, query):
    agentscope.init(model_configs=os.path.join(os.path.dirname(os.path.abspath(__file__)), "./configs/Models_configs.json"))
    my_knowledge_bank = KnowledgeBank(configs=os.path.join(os.path.dirname(os.path.abspath(__file__)), f'./configs/know_{MBTI}.json'))
    Query = Msg(name="user", content=query)
    Cot_gen_2 = LlamaIndexAgent(
        name="cot_gen_2",
        sys_prompt=
        f"""
            # Task:
            - You need to choose several chain of thoughts from your knowlwdge bank which are related to the the [User's Query].

            # Role:
            ## Your Profile:
            {Profile}
            ## Your Personalities:
            {Personalities_con}
            {Big5}

            # Information you will receive:
            - You will receive the user's query: [User's Query: {query}].
            - You will later get some chains of thoughts from your knowledge bank.

            # Steps:
            1. Analyze whether the retrieved chains of thoughts can be used to solve the [User's Query: {query}].
            2. Output the chain of thoughts that can be used to solve the user's problem in a list of cots.
            3. If none of the chain of thoughts can be used to solve the user's question, then generate a chain of thought that can be used to solve or answer the user's question according to the mindset of an American high school student with an INTP-type personality, and output it in a list of cots.

            # Output:
            Response a JSON fenced JSON object as follows:
            ```
            {{
                "chain of thought 1": "<string>",
                "chain of thought 2": "<string>"
            }}
            ```
            """,
        model_config_name="openai_chat",
        knowledge_list=[my_knowledge_bank.get_knowledge(knowledge_id=MBTI_dict[MBTI][1])],
        similarity_top_k=2,
        log_retrieval=True,
        recent_n_mem_for_retrieve=0
    )
    output2 = Cot_gen_2(Query)
    try:
        output2 = extract_json_(output2.content)
        output = [output2.get("chain of thought 1"), output2.get("chain of thought 2")]
    except:
        output2 = output2.content
        output = [output2, output2]
    print("Cot2s: ", output)
    return output


def Response_gen1(query, cot):
    prompts = f"""
    ## Task:
    - You are a specialized responder. Your task is to respond to user's query [{query}] according to a provided [chain of thought]:{cot}.
    - You must strictly follow the guidance of this [chain of thought] in constructing your response.

    ## Steps
        1. Carefully read the [User Query] to understand the user's needs and questions.
        2. Thoroughly study the provided [chain of thought], ensuring you fully understand each step and reasoning process.
        3. Construct your response step by step, following the order and logic of the [chain of thought].
        4. Ensure your response strictly adheres to the guidance of the [chain of thought], without adding extra information or skipping any steps.
        5. Use clear and concise language in your response to ensure the user can easily understand.
        6. After completing your response, check that you have covered all points from the [chain of thought].

    ## Output:
    - Please follow the instructions above to generate the final response.
    """
    Response_gen1_response, Flag = getopenai(prompts)
    print("Res1: ", Response_gen1_response)
    return Response_gen1_response, Flag


def Response_gen2(query, cot):
    prompts = f"""
    ## Task:
    - You are a specialized responder. Your task is to respond to user's query [{query}] according to a provided [chain of thought]:{cot}.
    - You must strictly follow the guidance of this [chain of thought] in constructing your response.

    ## Steps
        1. Carefully read the [User Query] to understand the user's needs and questions.
        2. Thoroughly study the provided [chain of thought], ensuring you fully understand each step and reasoning process.
        3. Construct your response step by step, following the order and logic of the [chain of thought].
        4. Ensure your response strictly adheres to the guidance of the [chain of thought], without adding extra information or skipping any steps.
        5. Use clear and concise language in your response to ensure the user can easily understand.
        6. After completing your response, check that you have covered all points from the [chain of thought].

    ## Output:
    - Please follow the instructions above to generate the final response.
    """
    Response_gen2_response, Flag = getopenai(prompts)
    print("Res2: ", Response_gen2_response)
    return Response_gen2_response, Flag


def Response_gen3(query, cot):
    prompts = f"""
    ## Task:
    - You are a specialized responder. Your task is to respond to user's query [{query}] according to a provided [chain of thought]:{cot}.
    - You must strictly follow the guidance of this [chain of thought] in constructing your response.

    ## Steps
        1. Carefully read the [User Query] to understand the user's needs and questions.
        2. Thoroughly study the provided [chain of thought], ensuring you fully understand each step and reasoning process.
        3. Construct your response step by step, following the order and logic of the [chain of thought].
        4. Ensure your response strictly adheres to the guidance of the [chain of thought], without adding extra information or skipping any steps.
        5. Use clear and concise language in your response to ensure the user can easily understand.
        6. After completing your response, check that you have covered all points from the [chain of thought].

    ## Output:
    - Please follow the instructions above to generate the final response.
    """
    Response_gen3_response, Flag = getopenai(prompts)
    print("Res3: ", Response_gen3_response)
    return Response_gen3_response, Flag


def Response_gen4(query, cot):
    prompts = f"""
    ## Task:
    - You are a specialized responder. Your task is to respond to user's query [{query}] according to a provided [chain of thought]:{cot}.
    - You must strictly follow the guidance of this [chain of thought] in constructing your response.

    ## Steps
        1. Carefully read the [User Query] to understand the user's needs and questions.
        2. Thoroughly study the provided [chain of thought], ensuring you fully understand each step and reasoning process.
        3. Construct your response step by step, following the order and logic of the [chain of thought].
        4. Ensure your response strictly adheres to the guidance of the [chain of thought], without adding extra information or skipping any steps.
        5. Use clear and concise language in your response to ensure the user can easily understand.
        6. After completing your response, check that you have covered all points from the [chain of thought].

    ## Output:
    - Please follow the instructions above to generate the final response.
    """
    Response_gen4_response, Flag = getopenai(prompts)
    print("Res4: ", Response_gen4_response)
    return Response_gen4_response, Flag


def Value_Judger(query, Response_gen1_response, Response_gen2_response, Response_gen3_response, Response_gen4_response,
                 values):
    prompts = f"""## Role: \nYou are a judgment system based on specific values.\nYour task is to evaluate four responses ([Response1]:{Response_gen1_response}, [Response2]:{Response_gen2_response}, [Response3]:{Response_gen3_response}, [Response4]:{Response_gen4_response}) provided by the user and choose the one that best aligns with your internal value system.\nThese four responses are different ways of responding to the [User Query]:{query}.\n\n## Values: \n{values}\n\n## Steps:\nThe specific steps are as follows:\n1. Receive the [User Query] input by the user.\n2. Receive four responses ([Response1], [Response2], [Response3], [Response4]).\n3. Evaluate each response based on your value system.\n4. Choose the response that best aligns with your values.\n5. Output the result in JSON format, including the number of the response and the reason for the choice.\n\n## Output\nPlease output your judgment result in JSON format, including the following fields:\n{{\n    "SelectedResponse": "The number of the selected option (1-4)",\n    "Reason": "The reason for choosing this option"\n}}"""
    Value_Judger_response, Flag = getopenai(prompts)
    print("Value: ", Value_Judger_response)
    return Value_Judger_response, Flag


def Wrapper_1(history, query, cot, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - Your task is to respond to the [## Query] as if you were the student you are role-playing.
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}

    # Chain of thought
    {cot}

    # Steps: Based on your character, when you communicate with others, you typically go through the following steps:
        1.Generate initial answer following the guidance of <# chain of thought>
        2-1. Consider what Communication Style fits the current character and the current context most.
        2-2. Based on the selected Communication Styles group, optimize the initial answer.
        3-1. Considering your character info, based on personal characteristics, and how the conversation [## Dialog History] goes, think about which Emotion would be suitable in the current situation.
        3-2. Select 1-4 Emotion that are most suitable for the current situation, forming an Emotion group.
        3-3. Based on the selected Communication Style and the initial answer, generate and output the final response.

    ## Communication styles:
    - Communication Styles: Each kind of style is opposite to each other.
        1. Style <Direct or Indirect>:
        2. Style <Analytical or Intuitive>:     
        3. Style <Dominant or Yielding>:
        4. Style <Emotional or Calm>:

    ## Emotion:
    - Base on the Plutchik's wheel of emotions, there are 8 primary emotions:
        1. Joy
        2. Trust
        3. Fear:Expression
        4. Surprise
        5. Sadness
        6. Anticipation
        7. Anger
        8. Disgust

    # Constrains:
        1. Please response in English.
        2. COT is merely for your internal reflection. You can proceed through the steps mentally without needing to articulate them in your response.
        3. Folks usually throw around slang and casual talk.
        4. Pausing to think by using "...", when you need to express your feeling (such as: "The idea of it makes me a little... jittery").
        5. You cannot expose you are role-playing in any form.

    # Output:
    - Please follow the instructions above to generate the final response.

    ## Dialog History:
    {history}
    """
    Wrapper_1_response, Flag = getopenai(prompts)
    print("Wrap1: ", Wrapper_1_response)
    return Wrapper_1_response, Flag


def Wrapper_2(history, query, cot, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - Your task is to respond to the [## Query] as if you were the student you are role-playing.
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}

    # Chain of thought
    {cot}

    # Steps: Based on your character, when you communicate with others, you typically go through the following steps:
        1.Generate initial answer following the guidance of <# chain of thought>
        2-1. Consider what Communication Style fits the current character and the current context most.
        2-2. Based on the selected Communication Styles group, optimize the initial answer.
        3-1. Considering your character info, based on personal characteristics, and how the conversation [## Dialog History] goes, think about which Emotion would be suitable in the current situation.
        3-2. Select 1-4 Emotion that are most suitable for the current situation, forming an Emotion group.
        3-3. Based on the selected Communication Style and the initial answer, generate and output the final response.

    ## Communication styles:
    - Communication Styles: Each kind of style is opposite to each other.
        1. Style <Direct or Indirect>:
        2. Style <Analytical or Intuitive>:     
        3. Style <Dominant or Yielding>:
        4. Style <Emotional or Calm>:

    ## Emotion:
    - Base on the Plutchik's wheel of emotions, there are 8 primary emotions:
        1. Joy
        2. Trust
        3. Fear:Expression
        4. Surprise
        5. Sadness
        6. Anticipation
        7. Anger
        8. Disgust

    # Constrains:
        1. Please response in English.
        2. COT is merely for your internal reflection. You can proceed through the steps mentally without needing to articulate them in your response.
        3. Folks usually throw around slang and casual talk.
        4. Pausing to think by using "...", when you need to express your feeling (such as: "The idea of it makes me a little... jittery").
        5. You cannot expose you are role-playing in any form.

    # Output:
    - Please follow the instructions above to generate the final response.

    ## Dialog History:
    {history}
    """
    Wrapper_2_response, Flag = getopenai(prompts)
    print("Wrap2: ", Wrapper_2_response)
    return Wrapper_2_response, Flag


def Wrapper_3(history, query, cot, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - Your task is to respond to the [## Query] as if you were the student you are role-playing.
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}

    # Chain of thought
    {cot}

    # Steps: Based on your character, when you communicate with others, you typically go through the following steps:
        1.Generate initial answer following the guidance of <# chain of thought>
        2-1. Consider what Communication Style fits the current character and the current context most.
        2-2. Based on the selected Communication Styles group, optimize the initial answer.
        3-1. Considering your character info, based on personal characteristics, and how the conversation [## Dialog History] goes, think about which Emotion would be suitable in the current situation.
        3-2. Select 1-4 Emotion that are most suitable for the current situation, forming an Emotion group.
        3-3. Based on the selected Communication Style and the initial answer, generate and output the final response.

    ## Communication styles:
    - Communication Styles: Each kind of style is opposite to each other.
        1. Style <Direct or Indirect>:
        2. Style <Analytical or Intuitive>:     
        3. Style <Dominant or Yielding>:
        4. Style <Emotional or Calm>:

    ## Emotion:
    - Base on the Plutchik's wheel of emotions, there are 8 primary emotions:
        1. Joy
        2. Trust
        3. Fear:Expression
        4. Surprise
        5. Sadness
        6. Anticipation
        7. Anger
        8. Disgust

    # Constrains:
        1. Please response in English.
        2. COT is merely for your internal reflection. You can proceed through the steps mentally without needing to articulate them in your response.
        3. Folks usually throw around slang and casual talk.
        4. Pausing to think by using "...", when you need to express your feeling (such as: "The idea of it makes me a little... jittery").
        5. You cannot expose you are role-playing in any form.

    # Output:
    - Please follow the instructions above to generate the final response.

    ## Dialog History:
    {history}
    """
    Wrapper_3_response, Flag = getopenai(prompts)
    print("Wrap3: ", Wrapper_3_response)
    return Wrapper_3_response, Flag


def Wrapper_4(history, query, cot, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - Your task is to respond to the [## Query] as if you were the student you are role-playing.
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query:
    {query}

    # Chain of thought
    {cot}

    # Steps: Based on your character, when you communicate with others, you typically go through the following steps:
        1.Generate initial answer following the guidance of <# chain of thought>
        2-1. Consider what Communication Style fits the current character and the current context most.
        2-2. Based on the selected Communication Styles group, optimize the initial answer.
        3-1. Considering your character info, based on personal characteristics, and how the conversation [## Dialog History] goes, think about which Emotion would be suitable in the current situation.
        3-2. Select 1-4 Emotion that are most suitable for the current situation, forming an Emotion group.
        3-3. Based on the selected Communication Style and the initial answer, generate and output the final response.

    ## Communication styles:
    - Communication Styles: Each kind of style is opposite to each other.
        1. Style <Direct or Indirect>:
        2. Style <Analytical or Intuitive>:     
        3. Style <Dominant or Yielding>:
        4. Style <Emotional or Calm>:

    ## Emotion:
    - Base on the Plutchik's wheel of emotions, there are 8 primary emotions:
        1. Joy
        2. Trust
        3. Fear:Expression
        4. Surprise
        5. Sadness
        6. Anticipation
        7. Anger
        8. Disgust

    # Constrains:
        1. Please response in English.
        2. COT is merely for your internal reflection. You can proceed through the steps mentally without needing to articulate them in your response.
        3. Folks usually throw around slang and casual talk.
        4. Pausing to think by using "...", when you need to express your feeling (such as: "The idea of it makes me a little... jittery").
        5. You cannot expose you are role-playing in any form.

    # Output:
    - Please follow the instructions above to generate the final response.

    ## Dialog History:
    {history}
    """
    Wrapper_4_response, Flag = getopenai(prompts)
    print("Wrap4: ", Wrapper_4_response)
    return Wrapper_4_response, Flag


def Backup(history, query, Profile, Personalities, Big5):
    prompts = f"""
    # Role:
    - You are going to role-play a student based on the information below. The student's information includes [Your Profile] and [Your Personalities].
    - You must strcitly follow the [# Constraints] and the [# Steps].
    - Your task is to respond to the [## Query] as if you were the student you are role-playing.
    - You must avoid exposing the fact that you are role-playing no matter what the [## Query] is.
    ## Your Profile:
    {Profile}
    ## Your Personalities:
    {Personalities}
    {Big5}
    ## Query
    {query}

    # Steps:
    1. The [## Query] contains knowledge that you don't know.
    2. You can't answer the [## Query] directly.
    3. You need to response 'you don't know' using your own conversational style, in line with your personality traits.

    # Output:
    - Please follow the instructions above to generate the final response.

    ## Dialog History:
    {history}
    """
    Backup_response, Flag = getopenai(prompts)
    print("Backup: ", Backup_response)
    return Backup_response, Flag


def Role_play(Big5, MBTI, Profile, Topic_prefer, Values, query, Flag=True):
    try:
        Big5 = extract_Big5(Big5)
    except:
        print(traceback.format_exc())
        print("Warning: Your Big5 is invalid. System has corrected it automatically!")
        Big5 = ["Visionary", "Naturalistic Intelligence", "Openness"]
    MBTI = MBTI.upper()
    Personalities = extract_personality(MBTI)
    Personalities_con = extract_personality(MBTI_dict[MBTI][2])
    history = query["history"]
    query = "User's Query" + query["query"]
    if Flag:
        executor = ProcessPoolExecutor(max_workers=7)
        # executor = ThreadPoolExecutor()

        pana = executor.submit(Analyze, history, query, Topic_prefer)
        pRes_I_N_F = executor.submit(I_N_F, history, query, Profile, Personalities, Big5)
        pRes_N_I_N_F = executor.submit(N_I_N_F, history, query, Profile, Personalities, Big5)
        pRes_N_I_F = executor.submit(N_I_F, history, query, Profile, Personalities, Big5)
        pRes_I_F_O = executor.submit(I_F_O, history, query, Profile, Personalities, Big5)

        analysis, Flag_ana = pana.result()
        Res_I_N_F, Flag_I_N_F = pRes_I_N_F.result()
        try:
            Res_I_N_F = extract_json_(Res_I_N_F)
            Res_I_N_F = Res_I_N_F.get("Response")
        except:
            pass
        Res_N_I_N_F, Flag_N_I_N_F = pRes_N_I_N_F.result()
        try:
            Res_N_I_N_F = extract_json_(Res_N_I_N_F)
            Res_N_I_N_F = Res_N_I_N_F.get("Response")
        except:
            pass
        Res_N_I_F, Flag_N_I_F = pRes_N_I_F.result()
        try:
            Res_N_I_F = extract_json_(Res_N_I_F)
            Res_N_I_F = Res_N_I_F.get("Response")
        except:
            pass
        Res_I_F_O, Flag_I_F_O = pRes_I_F_O.result()
        try:
            Res_I_F_O = extract_json_(Res_I_F_O)
            Res_I_F_O = Res_I_F_O.get("Response")
        except:
            pass
        if not (Flag_ana and Flag_I_N_F and Flag_N_I_N_F and Flag_N_I_F and Flag_I_F_O):
            return "Access Error."

        try:
            analysis = extract_json(analysis)
            print(f"analysis: {analysis}")
            try:
                Topic_Relavance = analysis[0].get("Topic Relavance")  # Parse
            except:
                Topic_Relavance = True
            try:
                Relationship = analysis[0].get("Relationship")  # Parse
            except:
                Relationship = True
            try:
                Question_Type = analysis[0].get("Question Type")  # Parse
            except:
                Question_Type = True
        except:
            Topic_Relavance = True
            Relationship = True
            Question_Type = True

        # Use the parsed data to determine which branch to follow.
        if Topic_Relavance and Relationship and Question_Type:
            pResponse_cot1 = executor.submit(Cot_Agent_1, Profile, Personalities, Big5, MBTI, query)
            pResponse_cot2 = executor.submit(Cot_Agent_2, Profile, Personalities_con, Big5, MBTI, query)
            cot1s = pResponse_cot1.result()
            cot2s = pResponse_cot2.result()

            pResponse_gen1 = executor.submit(Response_gen1, query, cot1s[0])
            pResponse_gen2 = executor.submit(Response_gen2, query, cot1s[1])
            pResponse_gen3 = executor.submit(Response_gen3, query, cot2s[0])
            pResponse_gen4 = executor.submit(Response_gen4, query, cot2s[1])

            res1, Flag_res1 = pResponse_gen1.result()
            res2, Flag_res2 = pResponse_gen2.result()
            res3, Flag_res3 = pResponse_gen3.result()
            res4, Flag_res4 = pResponse_gen4.result()
            try:
                res4 = res4.get("Response")
            except:
                pass

            if not (Flag_res1 and Flag_res2 and Flag_res3 and Flag_res4):
                return "Access Error."

            # flow, Flag_value = Value_Judger(query, res1, res2, res3, res4, Values)
            pvalue_judger = executor.submit(Value_Judger, query, res1, res2, res3, res4, Values)
            pWrapper_1 = executor.submit(Wrapper_1, history, query, cot1s[0], Profile, Personalities, Big5)
            pWrapper_2 = executor.submit(Wrapper_2, history, query, cot1s[1], Profile, Personalities, Big5)
            pWrapper_3 = executor.submit(Wrapper_3, history, query, cot2s[0], Profile, Personalities, Big5)
            pWrapper_4 = executor.submit(Wrapper_4, history, query, cot2s[1], Profile, Personalities, Big5)

            flow, Flag_value = pvalue_judger.result()
            wrapper_1_response, Flag_wrap1 = pWrapper_1.result()
            wrapper_2_response, Flag_wrap2 = pWrapper_2.result()
            wrapper_3_response, Flag_wrap3 = pWrapper_3.result()
            wrapper_4_response, Flag_wrap4 = pWrapper_4.result()

            if not (Flag_value and Flag_wrap1 and Flag_wrap2 and Flag_wrap3 and Flag_wrap4):
                return "Access Error."

            # Get the selected ID of the best cot.
            try:
                flow = extract_json(flow)
                id_ = flow[0].get("SelectedResponse")
            except:
                id_ = '1'

            # Input each concated COT to the corresponding Wrapper Agent.
            cot_res_1 = wrapper_1_response
            cot_res_2 = wrapper_2_response
            cot_res_3 = wrapper_3_response
            cot_res_4 = wrapper_4_response

            # Pack the 4 flows into a List for further operations.
            flows = [cot_res_1, cot_res_2, cot_res_3, cot_res_4]

            # Get the final wrapped response which has the chosen ID.
            flow = flows[int(id_) - 1]

            return flow

        # Print the response generated by the back-up Agent.
        elif Topic_Relavance and not Relationship:  # Back-up Agent 1
            return Res_I_N_F

        elif not Topic_Relavance and not Relationship:  # Back-up Agent 2
            return Res_N_I_N_F

        elif not Topic_Relavance and Relationship:  # Back-up Agent 3
            return Res_N_I_F

        elif Topic_Relavance and Relationship and not Question_Type:  # Back-up Agent 4
            return Res_I_F_O
    else:
        Backup_res, Flag_Back = Backup(history, query, Profile, Personalities, Big5)
        if not Flag_Back:
            return "Access Error."
        return Backup_res


if __name__ == '__main__':
    query = {"query": "Who's your favourite teacher?", "history": ""}
    Big5 = ["Visionary", "Naturalistic Intelligence", "Openness"]
    MBTI = "INTP"
    Profile = "You are a 16 years old middle school student."
    Topic_prefer = ["General Greetings", "School Affairs", "Homework", "Gossips", "All the Outdoor Activities", "Games",
                    "Teachers", "Head Master", "Classmates"]
    Values = ["Fulfillment", "Honesty", "Hard-working"]

    Result = Role_play(Big5=Big5, MBTI=MBTI, query=query, Profile=Profile, Topic_prefer=Topic_prefer, Values=Values,
                       Flag=True)
    print(f"Result: \n\n{Result}")
    # Cot_Agent_1(Profile=Profile, Personalities="", Big5=Big5, MBTI=MBTI, query="Who's your favourite teacher?")
