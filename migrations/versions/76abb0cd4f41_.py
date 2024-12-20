"""empty message

Revision ID: 76abb0cd4f41
Revises: 0ad873169dec
Create Date: 2024-12-19 15:13:05.715795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76abb0cd4f41'
down_revision = '0ad873169dec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('restaurant_id', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_column('restaurant_id')

    # ### end Alembic commands ###
