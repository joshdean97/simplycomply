"""add filesize to doc

Revision ID: b651d723f6a3
Revises: 465c66edcea4
Create Date: 2024-12-13 07:30:39.944650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b651d723f6a3'
down_revision = '465c66edcea4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_size', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_column('file_size')

    # ### end Alembic commands ###
