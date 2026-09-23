"""Columnas de ingesta de la spec 003 (T-010).

- `external_ref.last_seen_at` y `retained_since`: desapariciones y registros retenidos (RF-50 a RF-55).
- `observation.invalid_reason`: imposible frente a ilegible (plan D-8, RF-48 y RF-49).
- `changed_at` en las tablas resueltas: hora de última actualización (RF-157).
- `match.stats_complete_at` y `disappeared_at`: ventana de revisión y desapariciones (RF-19 a RF-21, RF-50).

Todas las columnas nuevas admiten nulo: los datos de la 002 se conservan tal cual.

Revision ID: a1c0e3f5b701
Revises: 737618706e21
Create Date: 2026-09-23 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c0e3f5b701'
down_revision: Union[str, Sequence[str], None] = '737618706e21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('championship', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('event', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('external_ref', sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('external_ref', sa.Column('retained_since', sa.DateTime(timezone=True), nullable=True))
    op.add_column('identity', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('match', sa.Column('stats_complete_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('match', sa.Column('disappeared_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('match', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('match_map', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('observation', sa.Column('invalid_reason', sa.Enum('impossible', 'unreadable', name='invalid_reason', native_enum=False, create_constraint=True, length=32), nullable=True))
    op.add_column('placement', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('player', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('player_map_stats', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('roster_membership', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('season', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('standing', sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('standing', 'changed_at')
    op.drop_column('season', 'changed_at')
    op.drop_column('roster_membership', 'changed_at')
    op.drop_column('player_map_stats', 'changed_at')
    op.drop_column('player', 'changed_at')
    op.drop_column('placement', 'changed_at')
    op.drop_column('observation', 'invalid_reason')
    op.drop_column('match_map', 'changed_at')
    op.drop_column('match', 'changed_at')
    op.drop_column('match', 'disappeared_at')
    op.drop_column('match', 'stats_complete_at')
    op.drop_column('identity', 'changed_at')
    op.drop_column('external_ref', 'retained_since')
    op.drop_column('external_ref', 'last_seen_at')
    op.drop_column('event', 'changed_at')
    op.drop_column('championship', 'changed_at')
