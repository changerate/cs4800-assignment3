"""canonical paper fields for OpenAlex ingestion

Revision ID: d1f3a8c9b2e4
Revises: 8be2c6a4f1b7
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa


revision = "d1f3a8c9b2e4"
down_revision = "8be2c6a4f1b7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("research_papers", schema=None) as batch_op:
        batch_op.add_column(sa.Column("feed_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("doi", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("authors_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("publisher", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("is_open_access", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("oa_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("oa_url", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("landing_url", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("pdf_url", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("topic_tags_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("cited_by_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("source_provider", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("source_record_id", sa.String(length=64), nullable=True))
    op.create_index(
        op.f("ix_research_papers_doi"),
        "research_papers",
        ["doi"],
        unique=True,
    )
    op.create_index(
        "uq_research_papers_provenance",
        "research_papers",
        ["source_provider", "source_record_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_research_papers_provenance", table_name="research_papers")
    op.drop_index(op.f("ix_research_papers_doi"), table_name="research_papers")
    with op.batch_alter_table("research_papers", schema=None) as batch_op:
        batch_op.drop_column("source_record_id")
        batch_op.drop_column("source_provider")
        batch_op.drop_column("cited_by_count")
        batch_op.drop_column("topic_tags_json")
        batch_op.drop_column("pdf_url")
        batch_op.drop_column("landing_url")
        batch_op.drop_column("oa_url")
        batch_op.drop_column("oa_status")
        batch_op.drop_column("is_open_access")
        batch_op.drop_column("publisher")
        batch_op.drop_column("authors_json")
        batch_op.drop_column("doi")
        batch_op.drop_column("feed_summary")
