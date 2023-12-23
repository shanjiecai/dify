"""add assistant_name to Message

Revision ID: 89099f2c4968
Revises: 88072f0caa04
Create Date: 2023-12-22 03:27:30.769459

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89099f2c4968'
down_revision = '88072f0caa04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assistant_name', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_column('assistant_name')

    # ### end Alembic commands ###