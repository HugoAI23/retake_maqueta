"""Número de semana de los partidos de clasificatorio (spec 003, T-092; cambio C-13).

Revision ID: a1c0e3f5b705
Revises: a1c0e3f5b704
Create Date: 2026-09-23 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c0e3f5b705'
down_revision: Union[str, Sequence[str], None] = 'a1c0e3f5b704'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('match', sa.Column('week', sa.SmallInteger(), nullable=True))
    op.create_check_constraint(op.f('ck_match_week_positive'), 'match', 'week > 0')


def downgrade() -> None:
    op.drop_constraint(op.f('ck_match_week_positive'), 'match', type_='check')
    op.drop_column('match', 'week')
