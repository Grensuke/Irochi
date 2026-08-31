"""Initial schema

Revision ID: 85bbd9d419bc
Revises:
Create Date: 2026-08-31 07:30:23.967056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = '85bbd9d419bc'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'alerts',
        sa.Column('alert_id', UUID(as_uuid=True), nullable=False),
        sa.Column('detector_output_id', sa.String(), nullable=False),
        sa.Column('detector_id', sa.String(), nullable=False),
        sa.Column('threat_type', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_key', sa.String(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('severity_candidate', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('evidence_summary', sa.Text(), nullable=False),
        sa.Column('evidence', JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source_feature_references', JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('detector_version', sa.String(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('schema_version', sa.String(), nullable=False),
        sa.Column('update_count', sa.Integer(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('alert_id'),
        sa.CheckConstraint("entity_type IN ('source', 'destination', 'pair', 'connection')", name='chk_valid_entity_type'),
        sa.CheckConstraint("status IN ('new', 'investigating', 'closed', 'false_positive')", name='chk_valid_status')
    )


def downgrade() -> None:
    op.drop_table('alerts')
