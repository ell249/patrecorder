"""switchboards and rcd fields

Revision ID: f3a1c9d2b6e8
Revises: a1b2c3d4e5f6
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f3a1c9d2b6e8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

RCD_COLUMNS = [
    ('rcd_type', sa.String(20)),
    ('rcd_waveform', sa.String(10)),
    ('rcd_test_method', sa.String(20)),
    ('rcd_push_button_result', sa.String(10)),
    ('rcd_trip_time_0deg_ms', sa.String(20)),
    ('rcd_trip_time_0deg_result', sa.String(10)),
    ('rcd_trip_time_180deg_ms', sa.String(20)),
    ('rcd_trip_time_180deg_result', sa.String(10)),
]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'switchboard' not in tables:
        op.create_table(
            'switchboard',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('location', sa.String(255), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )

    appliance_cols = {col['name'] for col in inspector.get_columns('appliance')}
    if 'switchboard_id' not in appliance_cols:
        with op.batch_alter_table('appliance', schema=None) as batch_op:
            batch_op.add_column(sa.Column('switchboard_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                'fk_appliance_switchboard_id', 'switchboard', ['switchboard_id'], ['id']
            )

    test_record_cols = {col['name'] for col in inspector.get_columns('test_record')}
    with op.batch_alter_table('test_record', schema=None) as batch_op:
        for name, coltype in RCD_COLUMNS:
            if name not in test_record_cols:
                batch_op.add_column(sa.Column(name, coltype, nullable=True))


def downgrade():
    with op.batch_alter_table('test_record', schema=None) as batch_op:
        for name, _ in reversed(RCD_COLUMNS):
            batch_op.drop_column(name)

    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.drop_constraint('fk_appliance_switchboard_id', type_='foreignkey')
        batch_op.drop_column('switchboard_id')

    op.drop_table('switchboard')
