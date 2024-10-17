"""update tools original_url length

Revision ID: 1787fbae959a
Revises: eeb2e349e6ac
Create Date: 2024-08-09 08:01:12.817620

"""

import sqlalchemy as sa
from alembic import op

import models as models

# revision identifiers, used by Alembic.
revision = "1787fbae959a"
down_revision = "eeb2e349e6ac"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("tool_files", schema=None) as batch_op:
        batch_op.alter_column(
            "original_url", existing_type=sa.VARCHAR(length=255), type_=sa.String(length=2048), existing_nullable=True
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("tool_files", schema=None) as batch_op:
        batch_op.alter_column(
            "original_url", existing_type=sa.String(length=2048), type_=sa.VARCHAR(length=255), existing_nullable=True
        )

    # ### end Alembic commands ###
