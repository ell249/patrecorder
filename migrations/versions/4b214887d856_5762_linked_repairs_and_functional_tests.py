"""5762 linked repairs and functional tests

Revision ID: 4b214887d856
Revises: 36377f572972
Create Date: 2026-05-07 15:42:17.874136

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4b214887d856'
down_revision = '36377f572972'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    existing_cols = {col['name'] for col in inspector.get_columns('test_record')}

    if 'test_repair_link' not in tables:
        op.create_table(
            'test_repair_link',
            sa.Column('test_record_id',   sa.Integer(), nullable=False),
            sa.Column('repair_record_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['repair_record_id'], ['repair_record.id']),
            sa.ForeignKeyConstraint(['test_record_id'],   ['test_record.id']),
            sa.PrimaryKeyConstraint('test_record_id', 'repair_record_id'),
        )

    with op.batch_alter_table('test_record', schema=None) as batch_op:
        for col in ('repair_description', 'repaired_by', 'parts_replaced', 'post_repair_test'):
            if col in existing_cols:
                batch_op.drop_column(col)
        for n in range(1, 6):
            if f'func_test_{n}_method' not in existing_cols:
                batch_op.add_column(sa.Column(f'func_test_{n}_method', sa.String(500), nullable=True))
            if f'func_test_{n}_result' not in existing_cols:
                batch_op.add_column(sa.Column(f'func_test_{n}_result', sa.String(10), nullable=True))


def downgrade():
    with op.batch_alter_table('test_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('post_repair_test',   mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255), nullable=True))
        batch_op.add_column(sa.Column('repaired_by',        mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255), nullable=True))
        batch_op.add_column(sa.Column('repair_description', mysql.TEXT(collation='utf8mb4_unicode_ci'),                nullable=True))
        batch_op.add_column(sa.Column('parts_replaced',     mysql.TEXT(collation='utf8mb4_unicode_ci'),                nullable=True))
        for n in range(5, 0, -1):
            batch_op.drop_column(f'func_test_{n}_result')
            batch_op.drop_column(f'func_test_{n}_method')

    op.drop_table('test_repair_link')
