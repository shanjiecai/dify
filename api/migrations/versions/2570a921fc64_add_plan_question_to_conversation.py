"""add_plan_question_to_conversation

Revision ID: 2570a921fc64
Revises: e316be27d39c
Create Date: 2024-03-17 02:43:53.416494

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2570a921fc64'
down_revision = 'e316be27d39c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('plan_question_invoke_user', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('plan_question_invoke_user_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('plan_question_invoke_time', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=True))
        batch_op.add_column(sa.Column('plan_question_invoke_plan', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_column('plan_question_invoke_plan')
        batch_op.drop_column('plan_question_invoke_time')
        batch_op.drop_column('plan_question_invoke_user_id')
        batch_op.drop_column('plan_question_invoke_user')

    # ### end Alembic commands ###
