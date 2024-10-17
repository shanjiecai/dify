from typing import Optional

from extensions.ext_database import db
from models.plan_question import PlanQuestion


# 存储知识点问题
class PlanQuestionService:

    @classmethod
    def get(cls, plan: str) -> Optional[PlanQuestion]:
        plan_question = db.session.query(PlanQuestion).filter(PlanQuestion.plan == plan).first()
        return plan_question

    @classmethod
    def get_all(cls) -> list[PlanQuestion]:
        plan_questions = db.session.query(PlanQuestion).all()
        return plan_questions
