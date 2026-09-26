"""switchboard environment

Revision ID: b2e6d4a1c8f3
Revises: a7c4e0f2b9d1
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2e6d4a1c8f3'
down_revision = 'a7c4e0f2b9d1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {col['name'] for col in inspector.get_columns('switchboard')}

    if 'environment' not in existing_cols:
        with op.batch_alter_table('switchboard', schema=None) as batch_op:
            batch_op.add_column(sa.Column('environment', sa.String(20), nullable=True))


def downgrade():
    with op.batch_alter_table('switchboard', schema=None) as batch_op:
        batch_op.drop_column('environment')
