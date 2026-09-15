"""Add incidents table

Revision ID: 85bbd9d419bd
Revises: 85bbd9d419bc
Create Date: 2026-09-15 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = '85bbd9d419bd'
down_revision: Union[str, None] = '85bbd9d419bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'incidents',
        sa.Column('incident_id', UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_key', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_event_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('member_alert_ids', JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('distinct_threat_types', JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_breakdown', JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('stage_state', sa.String(), nullable=False),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('forecast_next_stage', sa.String(), nullable=True),
        sa.Column('forecast_note', sa.Text(), nullable=True),
        sa.Column('schema_version', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('incident_id'),
        sa.CheckConstraint("status IN ('open', 'closed')", name='chk_valid_incident_status'),
        sa.CheckConstraint("stage_state IN ('anomaly', 'suspicious', 'likely_attack', 'confirmed_attack')", name='chk_valid_stage_state')
    )
    
    op.add_column('alerts', sa.Column('incident_id', UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    op.drop_column('alerts', 'incident_id')
    op.drop_table('incidents')
