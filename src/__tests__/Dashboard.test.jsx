/**
 * CloudBoard – Dashboard Component Tests (Module 17)
 * Tests metric computation, alert banner, and suggested actions rendering.
 * Run with: npm test
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Dashboard from '../components/Dashboard';

const mockTasks = [
  {
    id: 'T-001', title: 'Setup CI', status: 'Done', priority: 'High',
    assigneeId: '1', estimatedHours: 8, actual_hours: 8,
    labels: [], subtasks: [], comments: [], description: '',
    isBlocked: false, blockedBy: [],
  },
  {
    id: 'T-002', title: 'Write Tests', status: 'Doing', priority: 'Medium',
    assigneeId: '2', estimatedHours: 4, actual_hours: 2,
    labels: [], subtasks: [], comments: [], description: '',
    isBlocked: false, blockedBy: [],
  },
  {
    id: 'T-003', title: 'Deploy to Prod', status: 'Todo', priority: 'Urgent',
    assigneeId: '1', estimatedHours: 32, actual_hours: 0,
    labels: [], subtasks: [], comments: [], description: '',
    isBlocked: true, blockedBy: ['T-001'],
  },
];

const mockUsers = [
  { id: '1', name: 'Sara', role: 'Owner' },
  { id: '2', name: 'Ali',  role: 'Developer' },
];

const noop = vi.fn();

describe('Dashboard Component', () => {
  beforeEach(() => {
    noop.mockClear();
  });

  it('renders the project health alert banner', () => {
    render(<Dashboard tasks={mockTasks} users={mockUsers} setTab={noop} updateTask={noop} />);
    expect(screen.getByText(/Project Phoenix Health Alert/i)).toBeDefined();
  });

  it('shows "Go to Kanban" button in the alert banner', () => {
    render(<Dashboard tasks={mockTasks} users={mockUsers} setTab={noop} updateTask={noop} />);
    const btn = screen.getByRole('button', { name: /Go to Kanban/i });
    expect(btn).toBeDefined();
  });

  it('calls setTab("kanban") when Go to Kanban is clicked', () => {
    const setTab = vi.fn();
    render(<Dashboard tasks={mockTasks} users={mockUsers} setTab={setTab} updateTask={noop} />);
    const btn = screen.getByRole('button', { name: /Go to Kanban/i });
    fireEvent.click(btn);
    expect(setTab).toHaveBeenCalledWith('kanban');
  });

  it('renders workload table with developer names', () => {
    render(<Dashboard tasks={mockTasks} users={mockUsers} setTab={noop} updateTask={noop} />);
    expect(screen.getByText('Sara')).toBeDefined();
    expect(screen.getByText('Ali')).toBeDefined();
  });

  it('renders Suggested Actions widget', () => {
    render(<Dashboard tasks={mockTasks} users={mockUsers} setTab={noop} updateTask={noop} />);
    expect(screen.getByText(/Suggested Actions/i)).toBeDefined();
  });

  it('renders developer workload section heading', () => {
    render(<Dashboard tasks={mockTasks} users={mockUsers} setTab={noop} updateTask={noop} />);
    expect(screen.getByText(/Developer Workloads/i)).toBeDefined();
  });

  it('shows blocked task count in workload widget', () => {
    render(<Dashboard tasks={mockTasks} users={mockUsers} setTab={noop} updateTask={noop} />);
    const blockers = screen.getAllByText(/blocked task/i);
    expect(blockers.length).toBeGreaterThan(0);
  });
});
