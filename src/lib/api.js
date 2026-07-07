/**
 * CloudBoard API Client
 */

const API_BASE = "http://localhost:8000/api/v1";

export const getTasks = async () => {
  const response = await fetch(`${API_BASE}/tasks`);
  if (!response.ok) throw new Error("Failed to fetch tasks");
  return response.json();
};

export const createTask = async (taskData) => {
  const response = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(taskData)
  });
  if (!response.ok) throw new Error("Failed to create task");
  return response.json();
};

export const updateTask = async (taskId, updateData) => {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData)
  });
  if (!response.ok) throw new Error("Failed to update task");
  return response.json();
};

export const deleteTask = async (taskId) => {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: "DELETE"
  });
  if (!response.ok) throw new Error("Failed to delete task");
  return true;
};
