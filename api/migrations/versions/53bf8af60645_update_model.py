"""update model

Revision ID: 53bf8af60645
Revises: 8e5588e6412e
Create Date: 2024-07-24 08:06:55.291031

"""

import sqlalchemy as sa
from alembic import op

import models as models

# revision identifiers, used by Alembic.
revision = "53bf8af60645"
down_revision = "8e5588e6412e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("embeddings", schema=None) as batch_op:
        batch_op.alter_column(
            "provider_name",
            existing_type=sa.VARCHAR(length=40),
            type_=sa.String(length=255),
            existing_nullable=False,
            existing_server_default=sa.text("''::character varying"),
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("embeddings", schema=None) as batch_op:
        batch_op.alter_column(
            "provider_name",
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=40),
            existing_nullable=False,
            existing_server_default=sa.text("''::character varying"),
        )

    # ### end Alembic commands ###
