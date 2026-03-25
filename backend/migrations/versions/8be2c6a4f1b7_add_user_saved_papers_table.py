"""add user saved papers table

Revision ID: 8be2c6a4f1b7
Revises: c4ab1f2e9d10
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa


revision = "8be2c6a4f1b7"
down_revision = "c4ab1f2e9d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_saved_papers",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("paper_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["research_papers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "paper_id"),
    )


def downgrade():
    op.drop_table("user_saved_papers")
