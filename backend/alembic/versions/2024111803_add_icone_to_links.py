"""add icone to links

Revision ID: 2024111803
Revises: 2024111802
Create Date: 2024-11-18 01:00:00

"""

from alembic import op
import sqlalchemy as sa


revision = "2024111803"
down_revision = "2024111802"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE links ADD COLUMN IF NOT EXISTS icone VARCHAR(255)")


def downgrade() -> None:
    op.execute("ALTER TABLE links DROP COLUMN IF EXISTS icone")
