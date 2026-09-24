"""Revisión de partidos finalizados guardada en la base (spec 003, cambio C-25; plan I-39).

`finished_checked_at` es la consulta al finalizar (RF-19) y `finished_reviews`, las revisiones
diarias ya hechas (RF-20). Los partidos que ya tenían todas sus estadísticas se dan por consultados
entonces; si ya llevaban más de 3 días jugados, con sus tres revisiones hechas.

Revision ID: a1c0e3f5b707
Revises: a1c0e3f5b706
Create Date: 2026-09-24 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c0e3f5b707'
down_revision: Union[str, Sequence[str], None] = 'a1c0e3f5b706'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('match', sa.Column('finished_checked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('match', sa.Column('finished_reviews', sa.SmallInteger(), server_default='0', nullable=False))
    op.execute("""
        UPDATE match m SET
            finished_checked_at = m.stats_complete_at,
            finished_reviews = CASE
                WHEN (SELECT s.scheduled_at FROM match_schedule s WHERE s.match_id = m.id ORDER BY s.seq DESC LIMIT 1)
                     < m.stats_complete_at - INTERVAL '3 days' THEN 3
                ELSE 0 END
        WHERE m.status = 'finished' AND m.stats_complete_at IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_column('match', 'finished_reviews')
    op.drop_column('match', 'finished_checked_at')
