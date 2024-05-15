# 串联起生成计划问题的整个流程
import datetime

from flask import Flask

from controllers.app_api.plan.generate_knowledge_point_question import generate_knowledge_point_question
from controllers.app_api.plan.judge_plan import judge_plan
from extensions.ext_database import db
from models.model import Conversation
from models.plan_question import PlanQuestion
from mylogger import logger
from services.plan_question_service import PlanQuestionService


def generate_plan_question_pipeline(query, conversation: Conversation, user: str, user_id: str, judge_res: str = None):
    # # 根据用户问题判断是否需要生成计划
    if not judge_res:
        judge_res = judge_plan(query)
    if judge_res == 'no' or judge_res.startswith('no'):
        return None
    else:
        # query neo4j
        # pass
        if PlanQuestionService.get(judge_res):
            plan_question = PlanQuestionService.get(judge_res)
            questions = plan_question.questions

            # logger.info(f"{plan_question.plan} {plan_question.questions}")
            db.session.add(plan_question)
            db.session.commit()

            _conversation = db.session.query(Conversation).filter(Conversation.id == conversation.id).first()
            _conversation.plan_question_invoke_plan = plan_question.plan
            _conversation.plan_question_invoke_user = user
            _conversation.plan_question_invoke_user_id = user_id
            _conversation.plan_question_invoke_time = datetime.datetime.utcnow()
            db.session.commit()
        else:
            questions = generate_knowledge_point_question(judge_res)
            # 将questions信息存到数据库中
            plan_question = PlanQuestion(
                plan=judge_res,
                questions=questions,
                created_at=datetime.datetime.utcnow(),
            )
            db.session.add(plan_question)
            db.session.commit()
            _conversation = db.session.query(Conversation).filter(Conversation.id == conversation.id).first()
            _conversation.plan_question_invoke_plan = judge_res
            _conversation.plan_question_invoke_user = user
            _conversation.plan_question_invoke_user_id = user_id
            _conversation.plan_question_invoke_time = datetime.datetime.utcnow()
            db.session.commit()
        logger.info(f"add plan_question_invoke_plan: {judge_res} to conversation {conversation.id} ")

        return questions


def plan_question_background(flask_app: Flask, query: str, conversation: Conversation, user: str, user_id: str, judge_plan_res: str = None):
    with flask_app.app_context():
        questions = generate_plan_question_pipeline(query, conversation, user, user_id, judge_plan_res)
        if questions is None:
            return
        logger.info(f"plan_question_background: {query} {questions}")


if __name__ == '__main__':
    import sys

    sys.path.append('/Users/jiecai/PycharmProjects/dify/api')
    from app import create_app

    app = create_app()
    with app.app_context():
        query = "I need to improve my coding skills to get a better job."
        print(generate_plan_question_pipeline(query))
