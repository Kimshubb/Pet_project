from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa79e97e1dee'
down_revision = 'fdadb0687bed'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('mpesa_transaction', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_mpesa_transaction_code', ['code'])


def downgrade():
    with op.batch_alter_table('mpesa_transaction', schema=None) as batch_op:
        batch_op.drop_constraint('uq_mpesa_transaction_code', type_='unique')

