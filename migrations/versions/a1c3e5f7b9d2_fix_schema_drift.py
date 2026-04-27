"""fix schema drift — column lengths and orphaned columns

Revision ID: a1c3e5f7b9d2
Revises: 5a7786e7ce3f
Create Date: 2026-04-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'a1c3e5f7b9d2'
down_revision = '5a7786e7ce3f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.alter_column('asset_number',
               existing_type=mysql.VARCHAR(length=64),
               type_=sa.String(length=255),
               existing_nullable=False)
        batch_op.alter_column('class_type',
               existing_type=mysql.VARCHAR(length=32),
               type_=sa.String(length=50),
               existing_nullable=True)
        batch_op.alter_column('supply_type',
               existing_type=mysql.VARCHAR(length=32),
               type_=sa.String(length=50),
               existing_nullable=True)
        # created_at is kept — retained in model

    with op.batch_alter_table('retest_rule', schema=None) as batch_op:
        batch_op.alter_column('class_type',
               existing_type=mysql.VARCHAR(length=32),
               type_=sa.String(length=50),
               existing_nullable=True)
        batch_op.alter_column('supply_type',
               existing_type=mysql.VARCHAR(length=64),
               type_=sa.String(length=50),
               existing_nullable=True)
        batch_op.drop_column('description')
        batch_op.drop_column('priority')

    with op.batch_alter_table('tester', schema=None) as batch_op:
        batch_op.alter_column('full_name',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.String(length=120),
               existing_nullable=False)
        batch_op.alter_column('certificate_number',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.String(length=120),
               existing_nullable=False)


def downgrade():
    with op.batch_alter_table('tester', schema=None) as batch_op:
        batch_op.alter_column('certificate_number',
               existing_type=sa.String(length=120),
               type_=mysql.VARCHAR(length=255),
               existing_nullable=False)
        batch_op.alter_column('full_name',
               existing_type=sa.String(length=120),
               type_=mysql.VARCHAR(length=255),
               existing_nullable=False)

    with op.batch_alter_table('retest_rule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('description', sa.String(length=255), nullable=True))
        batch_op.alter_column('supply_type',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=64),
               existing_nullable=True)
        batch_op.alter_column('class_type',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=32),
               existing_nullable=True)

    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.alter_column('supply_type',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=32),
               existing_nullable=True)
        batch_op.alter_column('class_type',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=32),
               existing_nullable=True)
        batch_op.alter_column('asset_number',
               existing_type=sa.String(length=255),
               type_=mysql.VARCHAR(length=64),
               existing_nullable=False)
