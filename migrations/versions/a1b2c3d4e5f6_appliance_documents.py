"""appliance documents

Revision ID: a1b2c3d4e5f6
Revises: 36377f572972
Create Date: 2026-06-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '4b214887d856'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'appliance_document',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('appliance_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('filepath', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['appliance_id'], ['appliance.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, receipt_filepath FROM appliance WHERE receipt_filepath IS NOT NULL")
    )
    for row in rows:
        fname = row[1].rsplit('/', 1)[-1]
        bind.execute(
            sa.text(
                "INSERT INTO appliance_document (appliance_id, filename, filepath) "
                "VALUES (:aid, :fn, :fp)"
            ),
            {"aid": row[0], "fn": fname, "fp": row[1]},
        )

    existing = {col['name'] for col in sa.inspect(bind).get_columns('appliance')}
    if 'receipt_filepath' in existing:
        with op.batch_alter_table('appliance', schema=None) as batch_op:
            batch_op.drop_column('receipt_filepath')


def downgrade():
    with op.batch_alter_table('appliance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('receipt_filepath', sa.String(255), nullable=True))

    op.drop_table('appliance_document')
