"""add_dataset_update_social_agent

Revision ID: 48dbcfae4bb8
Revises: 408176b91ad3
Create Date: 2024-07-19 03:07:03.945410

"""
import sqlalchemy as sa
from alembic import op

import models as models

# revision identifiers, used by Alembic.
revision = '48dbcfae4bb8'
down_revision = '8782057ff0dc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dataset_update_real_time_social_agent',
    sa.Column('id', models.StringUUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('dataset_id', models.StringUUID(), nullable=False),
    sa.Column('app_id', models.StringUUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('last_updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('last_update_message_id', models.StringUUID(), nullable=True),
    sa.Column('last_update_message_updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name='dataset_update_real_time_social_agent_pkey')
    )
    with op.batch_alter_table('dataset_update_real_time_social_agent', schema=None) as batch_op:
        batch_op.create_index('dataset_update_real_time_social_agent_dataset_id_idx', ['dataset_id'], unique=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dataset_update_real_time_social_agent', schema=None) as batch_op:
        batch_op.drop_index('dataset_update_real_time_social_agent_dataset_id_idx')

    op.drop_table('dataset_update_real_time_social_agent')
    # ### end Alembic commands ###
