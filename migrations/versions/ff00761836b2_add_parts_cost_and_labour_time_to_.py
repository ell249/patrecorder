"""add parts cost and labour time to repair record

Revision ID: ff00761836b2
Revises: 29c092952bac
Create Date: 2026-04-27 10:22:39.354664

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ff00761836b2'
down_revision = '29c092952bac'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('repair_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parts_cost', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('labour_minutes', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('repair_record', schema=None) as batch_op:
        batch_op.drop_column('labour_minutes')
        batch_op.drop_column('parts_cost')
