"""initial users and research papers

Revision ID: c4ab1f2e9d10
Revises:
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa


revision = "c4ab1f2e9d10"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)
        batch_op.create_index(batch_op.f("ix_users_username"), ["username"], unique=True)

    op.create_table(
        "research_papers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("venue", sa.String(length=200), nullable=True),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("research_papers", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_research_papers_topic"), ["topic"], unique=False
        )


def downgrade():
    with op.batch_alter_table("research_papers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_research_papers_topic"))
    op.drop_table("research_papers")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_username"))
        batch_op.drop_index(batch_op.f("ix_users_email"))
    op.drop_table("users")
