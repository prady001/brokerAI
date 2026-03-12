"""Adiciona endereço/CEP ao cliente e flag de menor condutor à apólice.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-10
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("cep", sa.String(9), nullable=True))
    op.add_column("clients", sa.Column("address", sa.String(), nullable=True))
    op.add_column("policies", sa.Column("minor_driver", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("clients", "cep")
    op.drop_column("clients", "address")
    op.drop_column("policies", "minor_driver")
