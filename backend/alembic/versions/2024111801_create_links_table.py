"""create links table

Revision ID: 2024111801
Revises:
Create Date: 2024-11-18 00:00:00

"""

from alembic import op
import sqlalchemy as sa


revision = "2024111801"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(op.f("ix_links_id"), "links", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_links_id"), table_name="links")
    op.drop_table("links")
