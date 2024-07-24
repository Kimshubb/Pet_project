"""Altered mpesatable correctly

Revision ID: d16a8dccca48
Revises: fa79e97e1dee
Create Date: 2024-07-01 07:40:36.009838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd16a8dccca48'
down_revision = 'fa79e97e1dee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite to alter constraints
    with op.batch_alter_table('mpesa_transaction', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_code', ['code'])

def downgrade() -> None:
    # Use batch mode for SQLite to drop constraints
    with op.batch_alter_table('mpesa_transaction', schema=None) as batch_op:
        batch_op.drop_constraint('uq_code', type_='unique')