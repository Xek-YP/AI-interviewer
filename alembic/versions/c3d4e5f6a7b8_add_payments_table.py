"""Add payments table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-29 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

payment_status_enum = postgresql.ENUM(
    'pending',
    'success',
    'failed',
    name='paymentstatus',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'telegram_payment_charge_id',
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            'provider_payment_charge_id',
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('total_amount', sa.Integer(), nullable=False),
        sa.Column('payload', sa.String(length=128), nullable=False),
        sa.Column('status', payment_status_enum, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_payment_charge_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('payments')
    payment_status_enum.drop(op.get_bind(), checkfirst=True)
