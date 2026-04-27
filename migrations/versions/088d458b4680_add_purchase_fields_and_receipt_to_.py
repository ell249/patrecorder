"""add purchase fields and receipt to appliance

Revision ID: 088d458b4680
Revises: 3b480bc6a78a
Create Date: 2026-04-27 10:07:15.279747

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '088d458b4680'
down_revision = '3b480bc6a78a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('serial_number', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('purchase_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('purchase_price', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('receipt_filepath', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.drop_column('receipt_filepath')
        batch_op.drop_column('purchase_price')
        batch_op.drop_column('purchase_date')
        batch_op.drop_column('serial_number')
