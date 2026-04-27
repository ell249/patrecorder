"""add disposal fields to appliance

Revision ID: 29c092952bac
Revises: 088d458b4680
Create Date: 2026-04-27 10:14:02.452095

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '29c092952bac'
down_revision = '088d458b4680'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('disposal_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('disposal_price', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('disposal_comment', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.drop_column('disposal_comment')
        batch_op.drop_column('disposal_price')
        batch_op.drop_column('disposal_date')
