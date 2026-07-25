"""
Unit tests for CloudBoard GraphQL Gateway (Module 7).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_graphql_query_tasks():
    query = """
    query {
      tasks {
        id
        title
        status
        priority
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "tasks" in data["data"]
    assert len(data["data"]["tasks"]) > 0


def test_graphql_query_projects():
    query = """
    query {
      projects {
        id
        name
        key
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "projects" in data["data"]


def test_graphql_mutation_create_task():
    mutation = """
    mutation {
      createTask(title: "GraphQL Test Task", description: "Created via GraphQL mutation", priority: "High") {
        id
        title
        priority
        status
      }
    }
    """
    response = client.post("/graphql", json={"query": mutation})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["createTask"]["title"] == "GraphQL Test Task"
    assert data["data"]["createTask"]["priority"] == "High"
