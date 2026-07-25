"""
CloudBoard – GraphQL Gateway Router (Module 7).
Provides a unified GraphQL query and mutation interface powered by Strawberry GraphQL.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional
import time

# --- GraphQL Types ---

@strawberry.type
class TaskType:
    id: str
    title: str
    description: Optional[str] = ""
    status: str
    priority: str
    assignee_id: Optional[str] = "1"
    estimated_hours: int = 8
    actual_hours: int = 0


@strawberry.type
class ProjectType:
    id: str
    name: str
    key: str
    description: Optional[str] = ""
    organization_id: str


@strawberry.type
class OrganizationType:
    id: str
    name: str
    slug: str
    owner_id: str


@strawberry.type
class SystemHealthType:
    status: str
    uptime_seconds: float
    database_status: str
    websocket_connections: int


# --- Mock / In-Memory Data Store ---
dummy_tasks = [
    TaskType(id="PHX-101", title="Setup FastAPI Backend", description="Initialize project structure and database", status="Done", priority="High", assignee_id="1", estimated_hours=12, actual_hours=12),
    TaskType(id="PHX-102", title="Implement WebSocket Gateway", description="Real-time task synchronization across clients", status="Done", priority="Urgent", assignee_id="1", estimated_hours=8, actual_hours=6),
    TaskType(id="PHX-103", title="GraphQL Gateway Integration", description="Single entry point API with Strawberry GraphQL", status="Doing", priority="High", assignee_id="2", estimated_hours=16, actual_hours=4),
    TaskType(id="PHX-104", title="Redis Cache & Rate Limiter", description="Implement sliding window token bucket rate limiting", status="Todo", priority="Medium", assignee_id="3", estimated_hours=10, actual_hours=0),
]

dummy_projects = [
    ProjectType(id="proj-1", name="CloudBoard Core Platform", key="PHX", description="Engineering Intelligence & Management Platform", organization_id="org-1"),
    ProjectType(id="proj-2", name="AI Co-Pilot Engine", key="AIC", description="Gemini-based task estimation & duplicate detection", organization_id="org-1"),
]


# --- Root Query ---

@strawberry.type
class Query:
    @strawberry.field
    def tasks(self, status: Optional[str] = None) -> List[TaskType]:
        """Fetch all tasks, optionally filtered by status (Todo, Doing, Done)."""
        if status:
            return [t for t in dummy_tasks if t.status.lower() == status.lower()]
        return dummy_tasks

    @strawberry.field
    def task(self, id: str) -> Optional[TaskType]:
        """Fetch a single task by ID."""
        for t in dummy_tasks:
            if t.id == id:
                return t
        return None

    @strawberry.field
    def projects(self) -> List[ProjectType]:
        """Fetch all engineering projects."""
        return dummy_projects

    @strawberry.field
    def search(self, query: str) -> List[TaskType]:
        """Search tasks by title or description."""
        q = query.lower()
        return [t for t in dummy_tasks if q in t.title.lower() or q in (t.description or "").lower()]

    @strawberry.field
    def system_health(self) -> SystemHealthType:
        """Fetch real-time platform health via GraphQL."""
        return SystemHealthType(
            status="healthy",
            uptime_seconds=1850.0,
            database_status="healthy",
            websocket_connections=1
        )


# --- Root Mutation ---

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_task(self, title: str, description: str = "", priority: str = "Medium", assignee_id: str = "1") -> TaskType:
        """Create a new task via GraphQL mutation."""
        new_id = f"PHX-{len(dummy_tasks) + 105}"
        new_task = TaskType(
            id=new_id,
            title=title,
            description=description,
            status="Todo",
            priority=priority,
            assignee_id=assignee_id,
            estimated_hours=8,
            actual_hours=0
        )
        dummy_tasks.append(new_task)
        return new_task

    @strawberry.mutation
    def update_task_status(self, id: str, status: str) -> Optional[TaskType]:
        """Update a task's status via GraphQL mutation."""
        for t in dummy_tasks:
            if t.id == id:
                t.status = status
                return t
        return None

    @strawberry.mutation
    def delete_task(self, id: str) -> bool:
        """Delete a task via GraphQL mutation."""
        global dummy_tasks
        initial_len = len(dummy_tasks)
        dummy_tasks = [t for t in dummy_tasks if t.id != id]
        return len(dummy_tasks) < initial_len


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
