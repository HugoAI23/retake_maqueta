"""relax match_slot origin check

Segunda migración de la spec 002 (fase F4): al borrar el partido de origen de un lado,
la clave foránea deja `origin_match_id` nulo pero no `origin_outcome`, y la restricción
anterior lo impedía. Ahora solo se exige que un origen lleve su resultado.

Revision ID: 737618706e21
Revises: 352a7a5a3f2f
Create Date: 2026-09-22 23:07:26.949223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '737618706e21'
down_revision: Union[str, Sequence[str], None] = '352a7a5a3f2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_match_slot_origin_complete"), "match_slot", type_="check")
    op.create_check_constraint(
        op.f("ck_match_slot_origin_complete"), "match_slot", "origin_match_id IS NULL OR origin_outcome IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("UPDATE match_slot SET origin_outcome = NULL WHERE origin_match_id IS NULL")
    op.drop_constraint(op.f("ck_match_slot_origin_complete"), "match_slot", type_="check")
    op.create_check_constraint(
        op.f("ck_match_slot_origin_complete"), "match_slot", "(origin_match_id IS NULL) = (origin_outcome IS NULL)"
    )

