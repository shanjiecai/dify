
from sqlalchemy.dialects.postgresql import JSONB, UUID

from extensions.ext_database import db

# from models.model import App, UploadFile


class PlanQuestion(db.Model):
    __tablename__ = 'plan_question'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='plan_question_pkey'),
        db.Index('plan_question_tenant_id_idx', 'plan'),
    )

    id = db.Column(UUID, server_default=db.text('uuid_generate_v4()'))
    # 不区分租户
    # tenant_id = db.Column(UUID, nullable=False)
    # questions是数组，一个计划有多个问题
    plan = db.Column(db.Text, nullable=False)  # 计划或知识点内容
    questions = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
