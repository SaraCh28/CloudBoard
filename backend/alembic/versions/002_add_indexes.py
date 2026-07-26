"""Alembic migration: add performance indexes (Module 18)."""
from alembic import op

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tasks: most common query is filter by status ordered by created_at
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])
    # Composite index for project-scoped board views
    op.create_index("ix_tasks_project_id_status", "tasks", ["project_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_tasks_project_id_status", table_name="tasks")
    op.drop_index("ix_tasks_created_at", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
