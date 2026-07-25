/**
 * CloudBoard GraphQL Client (Module 7)
 * Executes GraphQL queries and mutations against http://localhost:8005/graphql
 */

const GRAPHQL_ENDPOINT = "http://localhost:8005/graphql";

export const executeGraphQL = async (query, variables = {}) => {
  const response = await fetch(GRAPHQL_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables })
  });

  const result = await response.json();
  if (result.errors && result.errors.length > 0) {
    throw new Error(result.errors[0].message || "GraphQL Query Failed");
  }
  return result.data;
};

export const fetchGraphQLTasks = async () => {
  const query = `
    query GetTasks {
      tasks {
        id
        title
        description
        status
        priority
        estimatedHours
        actualHours
      }
    }
  `;
  const data = await executeGraphQL(query);
  return data.tasks;
};

export const createGraphQLTask = async (title, description = "", priority = "Medium") => {
  const mutation = `
    mutation CreateTask($title: String!, $description: String!, $priority: String!) {
      createTask(title: $title, description: $description, priority: $priority) {
        id
        title
        status
        priority
      }
    }
  `;
  const data = await executeGraphQL(mutation, { title, description, priority });
  return data.createTask;
};
