"""add repair_record and repair_photo tables

Revision ID: 3b480bc6a78a
Revises: 
Create Date: 2026-04-27 08:55:26.620847

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3b480bc6a78a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('repair_record',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('appliance_id', sa.Integer(), nullable=False),
    sa.Column('repair_date', sa.Date(), nullable=False),
    sa.Column('repaired_by', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('comments', sa.Text(), nullable=True),
    sa.Column('locked_by_test_date', sa.Date(), nullable=True),
    sa.Column('disposed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['appliance_id'], ['appliance.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('repair_photo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('repair_id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('filepath', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['repair_id'], ['repair_record.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('repair_photo')
    op.drop_table('repair_record')
