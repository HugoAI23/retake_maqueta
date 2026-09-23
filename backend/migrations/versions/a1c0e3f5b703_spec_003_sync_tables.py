"""Tablas de la obtención automática de la spec 003 (T-012).

Estado de las fuentes, tareas con fecha, peticiones del administrador (con un índice único
parcial que impide dos peticiones activas de lo mismo, RF-107 y RF-108), registro de
consultas, incidencias sin repeticiones (RF-147) y resúmenes diarios (RF-150 a RF-154).

Revision ID: a1c0e3f5b703
Revises: a1c0e3f5b702
Create Date: 2026-09-23 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1c0e3f5b703'
down_revision: Union[str, Sequence[str], None] = 'a1c0e3f5b702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('daily_summary',
    sa.Column('day', sa.Date(), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('day', name=op.f('pk_daily_summary'))
    )
    op.create_table('incident',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('source', sa.Enum('bp', 'wiki', 'cdl', name='source', native_enum=False, create_constraint=True, length=32), nullable=True),
    sa.Column('kind', sa.Enum('query_failed', 'data_rejected', 'query_forbidden', 'match_disappeared', 'record_retained', 'cancel_discrepancy', 'origin_blocked', name='kind', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('value_hash', sa.String(length=64), nullable=True),
    sa.Column('reason', sa.String(length=500), nullable=False),
    sa.Column('detail', sa.String(length=500), nullable=True),
    sa.Column('first_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('repetitions', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('repetitions >= 1', name=op.f('ck_incident_repetitions_positive')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_incident')),
    sa.UniqueConstraint('source', 'kind', 'subject', 'value_hash', 'reason', name='uq_incident_identity', postgresql_nulls_not_distinct=True)
    )
    op.create_index(op.f('ix_incident_last_at'), 'incident', ['last_at'], unique=False)
    op.create_table('source_state',
    sa.Column('source', sa.Enum('bp', 'wiki', 'cdl', name='source', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('job', sa.Enum('initial_load', 'live', 'pre_match', 'regular', 'finished_matches', 'history', 'daily_summary', 'cleanup', name='job', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_item_count', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('source', 'job', name=op.f('pk_source_state'))
    )
    op.create_table('sync_job',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('key', sa.String(length=128), nullable=False),
    sa.Column('kind', sa.Enum('initial_load', 'live', 'pre_match', 'regular', 'finished_matches', 'history', 'daily_summary', 'cleanup', name='kind', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('done_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('attempts', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('last_error', sa.String(length=500), nullable=True),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_sync_job_attempts_not_negative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sync_job')),
    sa.UniqueConstraint('key', name=op.f('uq_sync_job_key'))
    )
    op.create_index(op.f('ix_sync_job_due_at'), 'sync_job', ['due_at'], unique=False)
    op.create_table('sync_request',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.Enum('source_refresh', 'history_reread', name='kind', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('source', sa.Enum('bp', 'wiki', 'cdl', name='source', native_enum=False, create_constraint=True, length=32), nullable=True),
    sa.Column('status', sa.Enum('pending', 'running', 'done', name='status', native_enum=False, create_constraint=True, length=32), server_default='pending', nullable=False),
    sa.Column('result', sa.Enum('success', 'partial', 'failure', 'forbidden', name='result', native_enum=False, create_constraint=True, length=32), nullable=True),
    sa.Column('incident_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=True),
    sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(status = 'done') = (result IS NOT NULL)", name=op.f('ck_sync_request_result_when_done')),
    sa.CheckConstraint('incident_count >= 0', name=op.f('ck_sync_request_incident_count_not_negative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sync_request'))
    )
    op.create_index('uq_sync_request_active', 'sync_request', [sa.literal_column('kind'), sa.literal_column("coalesce(source, '')")], unique=True, postgresql_where=sa.text("status IN ('pending', 'running')"))
    op.create_table('incident_day',
    sa.Column('incident_id', sa.BigInteger(), nullable=False),
    sa.Column('day', sa.Date(), nullable=False),
    sa.Column('repetitions', sa.Integer(), nullable=False),
    sa.CheckConstraint('repetitions >= 1', name=op.f('ck_incident_day_repetitions_positive')),
    sa.ForeignKeyConstraint(['incident_id'], ['incident.id'], name=op.f('fk_incident_day_incident_id_incident'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('incident_id', 'day', name=op.f('pk_incident_day'))
    )
    op.create_table('sync_run',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('source', sa.Enum('bp', 'wiki', 'cdl', name='source', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('job', sa.Enum('initial_load', 'live', 'pre_match', 'regular', 'finished_matches', 'history', 'daily_summary', 'cleanup', name='job', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('outcome', sa.Enum('success', 'partial', 'failure', 'forbidden', name='outcome', native_enum=False, create_constraint=True, length=32), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=True),
    sa.Column('request_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['request_id'], ['sync_request.id'], name=op.f('fk_sync_run_request_id_sync_request'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sync_run'))
    )
    op.create_index(op.f('ix_sync_run_finished_at'), 'sync_run', ['finished_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sync_run_finished_at'), table_name='sync_run')
    op.drop_table('sync_run')
    op.drop_table('incident_day')
    op.drop_index('uq_sync_request_active', table_name='sync_request', postgresql_where=sa.text("status IN ('pending', 'running')"))
    op.drop_table('sync_request')
    op.drop_index(op.f('ix_sync_job_due_at'), table_name='sync_job')
    op.drop_table('sync_job')
    op.drop_table('source_state')
    op.drop_index(op.f('ix_incident_last_at'), table_name='incident')
    op.drop_table('incident')
    op.drop_table('daily_summary')
