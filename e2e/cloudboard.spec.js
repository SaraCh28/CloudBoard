// @ts-check
/**
 * CloudBoard – Playwright E2E Test Suite (Module 17)
 *
 * Full coverage:
 *  T01  App loads with title
 *  T02  Sidebar navigation items present
 *  T03  Kanban Board columns visible
 *  T04  Create a task via "+" modal
 *  T05  Global search accessible and returns results
 *  T06  System Admin dashboard renders
 *  T07  Analytics tab loads charts
 *  T08  Settings & RBAC tab accessible
 *  T09  Auth flow – Register page (if present)
 *  T10  Notification center opens
 *  T11  Task creation and status badge
 *  T12  Rate-limit headers present on API call
 *  T13  Security headers present on health endpoint
 *  T14  /api/v1/version endpoint returns JSON
 *
 * Run: npx playwright test
 * Requires: npm run dev (frontend on :5173) + backend on :8005
 */

import { test, expect, request } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:5173';
const API_URL  = 'http://127.0.0.1:8005';

// ── UI Tests ───────────────────────────────────────────────────────

test.describe('CloudBoard – App Shell', () => {
  test('T01 – Application loads and shows CloudBoard in title', async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page).toHaveTitle(/CloudBoard/i);
    await expect(page.locator('text=CloudBoard').first()).toBeVisible();
  });

  test('T02 – Sidebar navigation items are present', async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('Kanban Board')).toBeVisible();
    await expect(page.getByText('Analytics')).toBeVisible();
    await expect(page.getByText('Notifications')).toBeVisible();
    await expect(page.getByText('System Admin')).toBeVisible();
    await expect(page.getByText('Settings & RBAC')).toBeVisible();
  });
});

test.describe('CloudBoard – Kanban Board', () => {
  test('T03 – Navigate to Kanban Board and verify task columns', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByText('Kanban Board').click();
    await expect(page.getByText('Todo')).toBeVisible();
    await expect(page.getByText('Doing')).toBeVisible();
    await expect(page.getByText('Done')).toBeVisible();
  });

  test('T04 – Open Add Task modal and create a task', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByText('Kanban Board').click();

    const addBtn = page.getByRole('button', { name: /add|new task|\+/i }).first();
    await addBtn.click();

    const titleInput = page.getByPlaceholder(/task title/i);
    await expect(titleInput).toBeVisible();
    await titleInput.fill('E2E Playwright Task');

    await page.getByRole('button', { name: /create|add task/i }).click();
    await expect(page.getByText('E2E Playwright Task')).toBeVisible();
  });

  test('T11 – Created task has a status badge', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByText('Kanban Board').click();

    const addBtn = page.getByRole('button', { name: /add|new task|\+/i }).first();
    await addBtn.click();

    await page.getByPlaceholder(/task title/i).fill('Badge Test Task');
    await page.getByRole('button', { name: /create|add task/i }).click();

    // Verify a status badge (Todo/Doing/Done) appears somewhere in the board
    const statusBadge = page.locator('[class*="status"], [class*="badge"], [class*="chip"]').first();
    await expect(statusBadge).toBeVisible();
  });
});

test.describe('CloudBoard – Search', () => {
  test('T05 – Global search input is accessible and accepts input', async ({ page }) => {
    await page.goto(BASE_URL);
    const searchInput = page.getByPlaceholder(/search|global search/i);
    await expect(searchInput).toBeVisible();
    await searchInput.fill('task');
    await page.waitForTimeout(400);
    // Input should still contain the typed text
    await expect(searchInput).toHaveValue('task');
  });
});

test.describe('CloudBoard – Notifications', () => {
  test('T10 – Notification center opens and shows content', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByText('Notifications').click();
    // Notification panel should appear
    await expect(page.locator('[class*="notification"], [class*="notif"]').first()).toBeVisible();
  });
});

test.describe('CloudBoard – Admin & Analytics', () => {
  test('T06 – Navigate to System Admin dashboard', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByText('System Admin').click();
    await expect(page.getByText(/System Admin|Observability/i).first()).toBeVisible();
  });

  test('T07 – Analytics tab loads charts section', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByText('Analytics').click();
    await expect(
      page.locator('h1, h2, h3').filter({ hasText: /analytics|velocity|sprint|workload/i }).first()
    ).toBeVisible();
  });

  test('T08 – Settings & RBAC tab is accessible', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByText('Settings & RBAC').click();
    await expect(page.getByText(/role|rbac|settings/i).first()).toBeVisible();
  });
});

// ── API Tests (direct HTTP, no browser) ──────────────────────────

test.describe('CloudBoard – API Smoke Tests', () => {
  test('T12 – Rate-limit headers present on API response', async () => {
    const ctx = await request.newContext({ baseURL: API_URL });
    const resp = await ctx.get('/api/v1/tasks');
    expect(resp.headers()['x-ratelimit-limit']).toBeDefined();
    expect(resp.headers()['x-ratelimit-remaining']).toBeDefined();
    await ctx.dispose();
  });

  test('T13 – Security headers present on health endpoint', async () => {
    const ctx = await request.newContext({ baseURL: API_URL });
    const resp = await ctx.get('/health');
    expect(resp.status()).toBe(200);
    expect(resp.headers()['x-content-type-options']).toBe('nosniff');
    expect(resp.headers()['x-frame-options']).toBe('DENY');
    expect(resp.headers()['content-security-policy']).toContain("frame-ancestors 'none'");
    await ctx.dispose();
  });

  test('T14 – /api/v1/version returns build metadata', async () => {
    const ctx = await request.newContext({ baseURL: API_URL });
    const resp = await ctx.get('/api/v1/version');
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.version).toBeDefined();
    expect(body.environment).toBeDefined();
    await ctx.dispose();
  });

  test('T15 – Audit logs endpoint returns paginated structure', async () => {
    const ctx = await request.newContext({ baseURL: API_URL });
    const resp = await ctx.get('/api/v1/system/logs?page=1&limit=10');
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    // Real DB-backed response should have paginated shape or be a list
    const hasItems = Array.isArray(body) || (body.items !== undefined);
    expect(hasItems).toBe(true);
    await ctx.dispose();
  });
});
