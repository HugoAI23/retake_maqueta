"""Logos y frescura de la spec 003 (T-011).

- `logo_image`: copia propia de cada logo, identificada por su huella SHA-256 (RF-65 a RF-70).
- `identity.logo_image_id`: la copia del logo de cada identidad; si se borra la copia, la identidad queda sin logo.
- `dataset_change`: último cambio de cada conjunto de datos (RF-155, RF-158).

Revision ID: a1c0e3f5b702
Revises: a1c0e3f5b701
Create Date: 2026-09-23 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c0e3f5b702'
down_revision: Union[str, Sequence[str], None] = 'a1c0e3f5b701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('dataset_change',
    sa.Column('dataset', sa.Enum('live', 'matches', 'standings', 'franchises', 'players', 'events', 'championships', 'season', name='dataset', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('last_changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('dataset', name=op.f('pk_dataset_change'))
    )
    op.create_table('logo_image',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('content', sa.LargeBinary(), nullable=False),
    sa.Column('media_type', sa.Enum('image/png', 'image/jpeg', 'image/webp', name='media_type', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('width', sa.Integer(), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('size_bytes > 0 AND size_bytes <= 1048576', name=op.f('ck_logo_image_size_range')),
    sa.CheckConstraint('width > 0 AND height > 0', name=op.f('ck_logo_image_dimensions_positive')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_logo_image'))
    )
    op.add_column('identity', sa.Column('logo_image_id', sa.String(length=64), nullable=True))
    op.create_foreign_key(op.f('fk_identity_logo_image_id_logo_image'), 'identity', 'logo_image', ['logo_image_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(op.f('fk_identity_logo_image_id_logo_image'), 'identity', type_='foreignkey')
    op.drop_column('identity', 'logo_image_id')
    op.drop_table('logo_image')
    op.drop_table('dataset_change')
