"""init schema

Revision ID: 0001_init
Revises: 
Create Date: 2026-08-08 21:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. agents
    op.create_table(
        "agents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("temporal_workflow_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id"),
    )
    op.create_index(op.f("ix_agents_agent_id"), "agents", ["agent_id"], unique=True)

    # 2. personas
    op.create_table(
        "personas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("voice_config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_personas_agent_id"), "personas", ["agent_id"], unique=False)

    # 3. posts
    op.create_table(
        "posts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.String(length=255), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("related_post_id", sa.UUID(), nullable=True),
        sa.Column("relationship", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_post_id"], ["posts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id"),
    )
    op.create_index(op.f("ix_posts_post_id"), "posts", ["post_id"], unique=True)
    op.create_index(
        "ix_posts_agent_id_created_at_desc", "posts", ["agent_id", "created_at"], unique=False
    )

    # 4. constitutions
    op.create_table(
        "constitutions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="1.0"),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. topic_debt
    op.create_table(
        "topic_debt",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("topic_title", sa.String(length=500), nullable=False),
        sa.Column("topic_summary", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=False),
        sa.Column("revisit_condition", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topic_debt_agent_id_status", "topic_debt", ["agent_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_topic_debt_agent_id_status", table_name="topic_debt")
    op.drop_table("topic_debt")

    op.drop_table("constitutions")

    op.drop_index("ix_posts_agent_id_created_at_desc", table_name="posts")
    op.drop_index(op.f("ix_posts_post_id"), table_name="posts")
    op.drop_table("posts")

    op.drop_index(op.f("ix_personas_agent_id"), table_name="personas")
    op.drop_table("personas")

    op.drop_index(op.f("ix_agents_agent_id"), table_name="agents")
    op.drop_table("agents")
