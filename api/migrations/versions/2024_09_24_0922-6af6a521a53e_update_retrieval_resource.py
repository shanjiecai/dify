"""update-retrieval-resource

Revision ID: 6af6a521a53e
Revises: ec3df697ebbb
Create Date: 2024-09-24 09:22:43.570120

"""

from alembic import op
import models as models
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6af6a521a53e"
down_revision = "d57ba9ebb251"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("dataset_retriever_resources", schema=None) as batch_op:
        batch_op.alter_column("document_id", existing_type=sa.UUID(), nullable=True)
        batch_op.alter_column("data_source_type", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column("segment_id", existing_type=sa.UUID(), nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("dataset_retriever_resources", schema=None) as batch_op:
        batch_op.alter_column("segment_id", existing_type=sa.UUID(), nullable=False)
        batch_op.alter_column("data_source_type", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column("document_id", existing_type=sa.UUID(), nullable=False)

    # ### end Alembic commands ###
