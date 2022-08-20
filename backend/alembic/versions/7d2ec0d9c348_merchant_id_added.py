"""merchant_id added

Revision ID: 7d2ec0d9c348
Revises: 1da50dd7c16d
Create Date: 2022-08-20 16:30:41.228097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d2ec0d9c348'
down_revision = '1da50dd7c16d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('merchant_id', sa.String(), nullable=True))
    op.drop_index('ix_users_email', table_name='users')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.drop_column('users', 'merchant_id')
    # ### end Alembic commands ###