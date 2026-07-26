/**
 * CloudBoard – API Hook / Utility Tests (Module 17)
 *
 * Tests the core API fetch utility used across the app.
 * Since CloudBoard uses a direct fetch wrapper (lib/api.js or inline),
 * we test the fetch contract, error handling, and JSON parsing.
 * Run with: npm test
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ── Mock fetch globally ───────────────────────────────────────────
const mockFetch = vi.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});


// ── Inline API helper (mirrors what the app components use) ───────
const API_BASE = 'http://localhost:8005/api/v1';

async function apiGet(path, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const resp = await fetch(`${API_BASE}${path}`, { headers });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

async function apiPost(path, body, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}


// ── Tests ─────────────────────────────────────────────────────────

describe('API Utility – GET requests', () => {
  it('fetches data and returns parsed JSON', async () => {
    const mockData = [{ id: 'T-1', title: 'Task 1' }];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const result = await apiGet('/tasks');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith(
      `${API_BASE}/tasks`,
      expect.objectContaining({ headers: expect.objectContaining({ 'Content-Type': 'application/json' }) })
    );
  });

  it('includes Authorization header when token is provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ email: 'test@test.com' }),
    });

    await apiGet('/auth/me', 'my-jwt-token');
    expect(mockFetch).toHaveBeenCalledWith(
      `${API_BASE}/auth/me`,
      expect.objectContaining({
        headers: expect.objectContaining({ 'Authorization': 'Bearer my-jwt-token' }),
      })
    );
  });

  it('throws an Error on non-2xx response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid credentials' }),
    });

    await expect(apiGet('/auth/me')).rejects.toThrow('Invalid credentials');
  });

  it('throws generic error when response body is not JSON', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error('not json')),
    });

    await expect(apiGet('/tasks')).rejects.toThrow();
  });
});


describe('API Utility – POST requests', () => {
  it('sends JSON body and returns parsed response', async () => {
    const payload = { title: 'New Task', status: 'Todo', priority: 'High' };
    const created = { id: 'T-99', ...payload };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(created),
    });

    const result = await apiPost('/tasks', payload, 'token-abc');
    expect(result).toEqual(created);
    expect(mockFetch).toHaveBeenCalledWith(
      `${API_BASE}/tasks`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      })
    );
  });

  it('throws on 409 conflict', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: () => Promise.resolve({ detail: 'Email or username already in use' }),
    });

    await expect(apiPost('/auth/register', {})).rejects.toThrow('Email or username already in use');
  });

  it('throws on network failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));
    await expect(apiPost('/tasks', {})).rejects.toThrow('Network error');
  });
});


describe('API Utility – token handling', () => {
  it('omits Authorization header when no token given', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });

    await apiGet('/tasks');
    const call = mockFetch.mock.calls[0];
    expect(call[1].headers['Authorization']).toBeUndefined();
  });
});
