from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b88f4d20087e'
down_revision = 'd7df7ead857d'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('term', schema=None) as batch_op:
        batch_op.drop_constraint('unique_term_name_year', type_='unique')

def downgrade():
    with op.batch_alter_table('term', schema=None) as batch_op:
        batch_op.create_unique_constraint('unique_term_name_year', ['name', 'year'])

