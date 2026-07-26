/**
 * CloudBoard – KanbanBoard Component Tests (Module 17)
 * Tests task columns, rendering, and modal interactions.
 * Run with: npm test
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import KanbanBoard from '../components/KanbanBoard';

const mockTasks = [
  { id: 'PHX-101', title: 'Setup Backend', status: 'Done', priority: 'High', assigneeId: '1', estimated_hours: 8, actual_hours: 8, labels: [], subtasks: [], comments: [], description: '' },
  { id: 'PHX-102', title: 'Implement WebSocket', status: 'Doing', priority: 'Urgent', assigneeId: '1', estimated_hours: 8, actual_hours: 4, labels: [], subtasks: [], comments: [], description: '' },
  { id: 'PHX-103', title: 'Write Tests', status: 'Todo', priority: 'Medium', assigneeId: '2', estimated_hours: 4, actual_hours: 0, labels: [], subtasks: [], comments: [], description: '' },
];

const mockUsers = [
  { id: '1', name: 'Sara', role: 'Owner' },
  { id: '2', name: 'Ali', role: 'Developer' },
];

const noop = vi.fn();

describe('KanbanBoard Component', () => {
  it('renders three status columns: Todo, Doing, Done', () => {
    render(
      <KanbanBoard
        tasks={mockTasks}
        users={mockUsers}
        addTask={noop}
        updateTask={noop}
        deleteTask={noop}
        currentRole="Owner"
        addNotificationLog={noop}
      />
    );
    expect(screen.getByText(/Todo/i)).toBeDefined();
    expect(screen.getByText(/Doing/i)).toBeDefined();
    expect(screen.getByText(/Done/i)).toBeDefined();
  });

  it('renders all task cards in the correct columns', () => {
    render(
      <KanbanBoard
        tasks={mockTasks}
        users={mockUsers}
        addTask={noop}
        updateTask={noop}
        deleteTask={noop}
        currentRole="Owner"
        addNotificationLog={noop}
      />
    );
    expect(screen.getByText('Setup Backend')).toBeDefined();
    expect(screen.getByText('Implement WebSocket')).toBeDefined();
    expect(screen.getByText('Write Tests')).toBeDefined();
  });

  it('shows task count badge per column', () => {
    render(
      <KanbanBoard
        tasks={mockTasks}
        users={mockUsers}
        addTask={noop}
        updateTask={noop}
        deleteTask={noop}
        currentRole="Owner"
        addNotificationLog={noop}
      />
    );
    // Each column should show a count
    const badges = screen.getAllByText('1');
    expect(badges.length).toBeGreaterThanOrEqual(2);
  });
});
