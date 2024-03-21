plan_question_template = """You need to sequentially ask the following questions. If the responses to these questions 
are already present in the previous interactions, you should not repeat them. Continue this process until you are 
confident that all the questions have been addressed by the user. Once you reach this point, please append 
the <finish_question> tag at the end of your current response. Here are the questions: {questions}"""

