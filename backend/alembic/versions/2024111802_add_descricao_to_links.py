"""add descricao to links

Revision ID: 2024111802
Revises: 2024111801
Create Date: 2024-11-18 00:10:00

"""

from alembic import op
import sqlalchemy as sa


revision = "2024111802"
down_revision = "2024111801"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE links ADD COLUMN IF NOT EXISTS descricao TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE links DROP COLUMN IF EXISTS descricao")
