"""Tablas de administración de la spec 003 (T-013).

Una sola cuenta (`admin_user.id = 1`, RF-121), sesiones guardadas por la huella de su
identificador (H-8) y bloqueo por origen tras 5 intentos fallidos (RF-127 a RF-133).

Revision ID: a1c0e3f5b704
Revises: a1c0e3f5b703
Create Date: 2026-09-23 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c0e3f5b704'
down_revision: Union[str, Sequence[str], None] = 'a1c0e3f5b703'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('admin_session',
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('origin', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('token_hash', name=op.f('pk_admin_session'))
    )
    op.create_index(op.f('ix_admin_session_expires_at'), 'admin_session', ['expires_at'], unique=False)
    op.create_table('admin_user',
    sa.Column('id', sa.SmallInteger(), server_default=sa.text('1'), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('id = 1', name=op.f('ck_admin_user_single_account')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_admin_user')),
    sa.UniqueConstraint('username', name=op.f('uq_admin_user_username'))
    )
    op.create_table('login_origin',
    sa.Column('origin', sa.String(length=64), nullable=False),
    sa.Column('failures', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('blocked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('failures >= 0', name=op.f('ck_login_origin_failures_not_negative')),
    sa.PrimaryKeyConstraint('origin', name=op.f('pk_login_origin'))
    )


def downgrade() -> None:
    op.drop_table('login_origin')
    op.drop_table('admin_user')
    op.drop_index(op.f('ix_admin_session_expires_at'), table_name='admin_session')
    op.drop_table('admin_session')
