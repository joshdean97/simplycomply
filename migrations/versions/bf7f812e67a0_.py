"""empty message

Revision ID: bf7f812e67a0
Revises: 57b5db34be92
Create Date: 2024-12-22 09:21:55.114054

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf7f812e67a0'
down_revision = '57b5db34be92'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('alert_time', sa.DateTime(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.drop_column('alert_time')

    # ### end Alembic commands ###
