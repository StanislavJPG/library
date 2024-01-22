"""empty message

Revision ID: a1aa1d3cabd0
Revises: 899caa39041d
Create Date: 2024-01-22 14:47:05.583149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1aa1d3cabd0'
down_revision: Union[str, None] = '899caa39041d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('book', sa.Column('url_orig', sa.String(), nullable=True))
    op.drop_constraint('book_url_key', 'book', type_='unique')
    op.alter_column('user', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.create_unique_constraint('book_url_key', 'book', ['url'])
    op.drop_column('book', 'url_orig')
    # ### end Alembic commands ###
