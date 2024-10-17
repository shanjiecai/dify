"""rename api provider credentials

Revision ID: 8ec536f3c800
Revises: ad472b61a054
Create Date: 2024-01-07 03:57:35.257545

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8ec536f3c800"
down_revision = "ad472b61a054"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("tool_api_providers", schema=None) as batch_op:
        batch_op.add_column(sa.Column("credentials_str", sa.Text(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("tool_api_providers", schema=None) as batch_op:
        batch_op.drop_column("credentials_str")

    # ### end Alembic commands ###
