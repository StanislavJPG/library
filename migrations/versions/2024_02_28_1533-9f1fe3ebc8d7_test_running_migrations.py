"""test running migrations

Revision ID: 9f1fe3ebc8d7
Revises: 0a8bc46a0718
Create Date: 2024-02-28 15:33:59.191733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f1fe3ebc8d7'
down_revision: Union[str, None] = '0a8bc46a0718'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
