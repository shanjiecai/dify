"""add node_execution_id into node_executions

Revision ID: 675b5321501b
Revises: 030f4915f36a
Create Date: 2024-08-12 10:54:02.259331

"""

import sqlalchemy as sa
from alembic import op

import models as models

# revision identifiers, used by Alembic.
revision = "675b5321501b"
down_revision = "030f4915f36a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("workflow_node_executions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("node_execution_id", sa.String(length=255), nullable=True))
        batch_op.create_index(
            "workflow_node_execution_id_idx",
            ["tenant_id", "app_id", "workflow_id", "triggered_from", "node_execution_id"],
            unique=False,
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("workflow_node_executions", schema=None) as batch_op:
        batch_op.drop_index("workflow_node_execution_id_idx")
        batch_op.drop_column("node_execution_id")

    # ### end Alembic commands ###
