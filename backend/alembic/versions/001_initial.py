"""Initial schema - companies, people, research, templates, chat, evaluations

Revision ID: 001_initial
Revises:
Create Date: 2025-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from pgvector.sqlalchemy import Vector

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'companies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False, index=True),
        sa.Column('domain', sa.String(500)),
        sa.Column('website', sa.String(1000)),
        sa.Column('industry', sa.String(200)),
        sa.Column('size', sa.String(100)),
        sa.Column('location', sa.String(500)),
        sa.Column('description', sa.Text),
        sa.Column('tech_stack', JSON),
        sa.Column('hiring_trends', JSON),
        sa.Column('summary', sa.Text),
        sa.Column('logo_url', sa.String(1000)),
        sa.Column('linkedin_url', sa.String(1000)),
        sa.Column('research_status', sa.String(50), default='pending'),
        sa.Column('research_completed_at', sa.DateTime),
        sa.Column('meta_data', JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'people',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('title', sa.String(500)),
        sa.Column('role_category', sa.String(200)),
        sa.Column('linkedin_url', sa.String(1000)),
        sa.Column('recent_posts', JSON),
        sa.Column('activity_summary', sa.Text),
        sa.Column('relevance_score', sa.Float, default=0.0),
        sa.Column('meta_data', JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'research_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('source_type', sa.String(100), nullable=False),
        sa.Column('source_url', sa.String(2000)),
        sa.Column('title', sa.String(1000)),
        sa.Column('content', sa.Text),
        sa.Column('content_embedding', Vector(768)),
        sa.Column('relevance_score', sa.Float, default=0.0),
        sa.Column('collected_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('meta_data', JSON),
    )
    op.create_index('ix_research_company_source', 'research_data', ['company_id', 'source_type'])

    op.create_table(
        'templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('template_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('target_person_id', UUID(as_uuid=True), sa.ForeignKey('people.id')),
        sa.Column('tone', sa.String(100)),
        sa.Column('context_used', JSON),
        sa.Column('evaluation_scores', JSON),
        sa.Column('meta_data', JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'conversations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('title', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('sources_used', JSON),
        sa.Column('evaluation_scores', JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'evaluations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('content_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('metric', sa.String(100), nullable=False),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('reasoning', sa.Text),
        sa.Column('sources_checked', JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_evaluations_content', 'evaluations', ['content_id', 'content_type'])
    op.create_index('ix_evaluations_agent_metric', 'evaluations', ['agent_type', 'metric'])

    op.create_table(
        'agent_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('input_data', JSON),
        sa.Column('output_data', JSON),
        sa.Column('error_message', sa.Text),
        sa.Column('tokens_used', sa.Integer),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_agent_runs_company_type', 'agent_runs', ['company_id', 'agent_type'])


def downgrade() -> None:
    op.drop_table('agent_runs')
    op.drop_table('evaluations')
    op.drop_table('chat_messages')
    op.drop_table('conversations')
    op.drop_table('templates')
    op.drop_table('research_data')
    op.drop_table('people')
    op.drop_table('companies')
