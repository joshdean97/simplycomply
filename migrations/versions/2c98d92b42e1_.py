"""empty message

Revision ID: 2c98d92b42e1
Revises: 55531d8dd9b3
Create Date: 2025-01-22 13:20:14.904067

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c98d92b42e1'
down_revision = '55531d8dd9b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('stripe_customer_id')

    # ### end Alembic commands ###
