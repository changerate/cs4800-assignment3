"""add title_summarized to research_papers

Revision ID: f3c8d9e0a1b2
Revises: e2a7b0c1d4f5
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa


revision = "f3c8d9e0a1b2"
down_revision = "e2a7b0c1d4f5"
branch_labels = None
depends_on = None


def upgrade():
    # IF NOT EXISTS: safe when the column was added manually or re-run.
    op.execute(
        sa.text(
            "ALTER TABLE research_papers ADD COLUMN IF NOT EXISTS title_summarized TEXT"
        )
    )


def downgrade():
    op.execute(
        sa.text("ALTER TABLE research_papers DROP COLUMN IF EXISTS title_summarized")
    )
