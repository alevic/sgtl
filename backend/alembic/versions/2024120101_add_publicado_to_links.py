"""add publicado to links

Revision ID: 2024120101
Revises: 2024111803_add_icone_to_links
Create Date: 2025-12-01
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2024120101"
down_revision = "2024111803"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "links",
        sa.Column(
            "publicado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("links", "publicado")
