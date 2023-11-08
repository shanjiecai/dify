"""add_api_based_extension

Revision ID: 968fff4c0ab9
Revises: b3a09c049e8e
Create Date: 2023-10-27 13:05:58.901858

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '968fff4c0ab9'
down_revision = '4ef156ca9c66'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.create_table('api_based_extensions',
    sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('tenant_id', postgresql.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('api_endpoint', sa.String(length=255), nullable=False),
    sa.Column('api_key', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name='api_based_extension_pkey')
    )
    with op.batch_alter_table('api_based_extensions', schema=None) as batch_op:
        batch_op.create_index('api_based_extension_tenant_idx', ['tenant_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    with op.batch_alter_table('api_based_extensions', schema=None) as batch_op:
        batch_op.drop_index('api_based_extension_tenant_idx')

    op.drop_table('api_based_extensions')

    # ### end Alembic commands ###
