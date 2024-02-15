"""add previous_summary into conversation

Revision ID: 4ef156ca9c66
Revises: ba0e29efe7a4
Create Date: 2023-10-22 14:42:42.622037

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4ef156ca9c66'
down_revision = 'ba0e29efe7a4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('previous_summary', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('previous_summary_updated_at', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_column('previous_summary_updated_at')
        batch_op.drop_column('previous_summary')

    # ### end Alembic commands ###
