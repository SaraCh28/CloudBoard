/**
 * CloudBoard API Client
 */

const API_BASE = "http://localhost:8005/api/v1";

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

export const uploadAttachment = async (taskId, file) => {
  const formData = new FormData();
  formData.append("task_id", taskId);
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/attachments/upload`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to upload attachment");
  }
  return response.json();
};

export const getTaskAttachments = async (taskId) => {
  const response = await fetch(`${API_BASE}/attachments/${taskId}`);
  if (!response.ok) return [];
  return response.json();
};

export const deleteAttachment = async (attachmentId) => {
  const response = await fetch(`${API_BASE}/attachments/${attachmentId}`, {
    method: "DELETE"
  });
  if (!response.ok) throw new Error("Failed to delete attachment");
  return response.json();
};

export const getSystemHealth = async () => {
  const response = await fetch(`${API_BASE}/system/health`);
  if (!response.ok) throw new Error("Failed to fetch system health");
  return response.json();
};

export const getSystemLogs = async () => {
  const response = await fetch(`${API_BASE}/system/logs`);
  if (!response.ok) throw new Error("Failed to fetch system logs");
  return response.json();
};

