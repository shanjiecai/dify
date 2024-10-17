"""add environment variable to workflow model

Revision ID: 8e5588e6412e
Revises: 6e957a32015b
Create Date: 2024-07-22 03:27:16.042533

"""

import sqlalchemy as sa
from alembic import op

import models as models

# revision identifiers, used by Alembic.
revision = "8e5588e6412e"
down_revision = "6e957a32015b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("workflows", schema=None) as batch_op:
        batch_op.add_column(sa.Column("environment_variables", sa.Text(), server_default="{}", nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("workflows", schema=None) as batch_op:
        batch_op.drop_column("environment_variables")

    # ### end Alembic commands ###
