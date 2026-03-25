"""topic field and subfield from OpenAlex primary_topic

Revision ID: e2a7b0c1d4f5
Revises: d1f3a8c9b2e4
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa


revision = "e2a7b0c1d4f5"
down_revision = "d1f3a8c9b2e4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("research_papers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("topic_field", sa.String(length=120), nullable=True)
        )
        batch_op.add_column(
            sa.Column("topic_subfield", sa.String(length=120), nullable=True)
        )
        batch_op.create_index(
            "ix_research_papers_topic_field", ["topic_field"], unique=False
        )


def downgrade():
    with op.batch_alter_table("research_papers", schema=None) as batch_op:
        batch_op.drop_index("ix_research_papers_topic_field")
        batch_op.drop_column("topic_subfield")
        batch_op.drop_column("topic_field")
