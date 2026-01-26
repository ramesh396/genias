"""add email verification and reset columns

Revision ID: cf52dea0dad3
Revises: 527375142a15
Create Date: 2026-01-21 13:01:59.859804
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cf52dea0dad3'
down_revision = '527375142a15'
branch_labels = None
depends_on = None


def upgrade():

    # ---------------- USERS TABLE ----------------
    with op.batch_alter_table('users', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'email_verified',
                sa.Boolean(),
                server_default=sa.text('false'),
                nullable=False
            )
        )

        batch_op.add_column(
            sa.Column(
                'email_verification_token',
                sa.String(length=200),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'reset_token',
                sa.String(length=200),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'reset_token_expiry',
                sa.DateTime(),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'role',
                sa.String(length=20),
                server_default='user',
                nullable=False
            )
        )

        batch_op.add_column(
            sa.Column(
                'created',
                sa.DateTime(),
                server_default=sa.text('NOW()'),
                nullable=False
            )
        )

        batch_op.create_index('ix_users_email', ['email'], unique=True)
        batch_op.create_index('ix_users_username', ['username'], unique=True)
        batch_op.create_index('ix_users_plan', ['plan'], unique=False)
        batch_op.create_index('ix_users_role', ['role'], unique=False)

    # ---------------- REMOVE TEMP DEFAULTS ----------------
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('email_verified', server_default=None)
        batch_op.alter_column('role', server_default=None)
        batch_op.alter_column('created', server_default=None)


def downgrade():

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_role')
        batch_op.drop_index('ix_users_plan')
        batch_op.drop_index('ix_users_username')
        batch_op.drop_index('ix_users_email')

        batch_op.drop_column('created')
        batch_op.drop_column('role')
        batch_op.drop_column('reset_token_expiry')
        batch_op.drop_column('reset_token')
        batch_op.drop_column('email_verification_token')
        batch_op.drop_column('email_verified')
