"""convert vi_casing vi_label polarity_pass to string

Revision ID: 5a7786e7ce3f
Revises: ff00761836b2
Create Date: 2026-04-27 10:39:53.460210

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5a7786e7ce3f'
down_revision = 'ff00761836b2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('test_record', schema=None) as batch_op:
        batch_op.alter_column('vi_casing',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.String(length=50),
               existing_nullable=True)
        batch_op.alter_column('vi_label',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.String(length=50),
               existing_nullable=True)
        batch_op.alter_column('polarity_pass',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.String(length=50),
               existing_nullable=True)


def downgrade():
    with op.batch_alter_table('test_record', schema=None) as batch_op:
        batch_op.alter_column('polarity_pass',
               existing_type=sa.String(length=50),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
        batch_op.alter_column('vi_label',
               existing_type=sa.String(length=50),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
        batch_op.alter_column('vi_casing',
               existing_type=sa.String(length=50),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
