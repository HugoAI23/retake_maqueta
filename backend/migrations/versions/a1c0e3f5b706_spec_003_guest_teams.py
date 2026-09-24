"""Equipos invitados (spec 003, cambios C-23 y C-24; plan I-38).

Una franquicia puede estar marcada como invitada (RF-117a de la 002), y se guarda cuándo se
consultaron por última vez su ficha y las de sus jugadores, que van una vez al mes (RF-18b).

Revision ID: a1c0e3f5b706
Revises: a1c0e3f5b705
Create Date: 2026-09-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c0e3f5b706'
down_revision: Union[str, Sequence[str], None] = 'a1c0e3f5b705'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('franchise', sa.Column('is_guest', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('franchise', sa.Column('guest_checked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('franchise', 'guest_checked_at')
    op.drop_column('franchise', 'is_guest')
