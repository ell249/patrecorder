"""appliance rcd fields

Revision ID: a7c4e0f2b9d1
Revises: f3a1c9d2b6e8
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a7c4e0f2b9d1'
down_revision = 'f3a1c9d2b6e8'
branch_labels = None
depends_on = None

RCD_COLUMNS = [
    ('rcd_type', sa.String(20)),
    ('rcd_waveform', sa.String(10)),
]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {col['name'] for col in inspector.get_columns('appliance')}

    with op.batch_alter_table('appliance', schema=None) as batch_op:
        for name, coltype in RCD_COLUMNS:
            if name not in existing_cols:
                batch_op.add_column(sa.Column(name, coltype, nullable=True))


def downgrade():
    with op.batch_alter_table('appliance', schema=None) as batch_op:
        for name, _ in reversed(RCD_COLUMNS):
            batch_op.drop_column(name)
