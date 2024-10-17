"""remove tool id from model invoke

Revision ID: 114eed84c228
Revises: c71211c8f604
Create Date: 2024-01-10 04:40:57.257824

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "114eed84c228"
down_revision = "c71211c8f604"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("tool_model_invokes", schema=None) as batch_op:
        batch_op.drop_column("tool_id")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("tool_model_invokes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tool_id", postgresql.UUID(), autoincrement=False, nullable=False))

    # ### end Alembic commands ###
