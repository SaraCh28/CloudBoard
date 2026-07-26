/**
 * CloudBoard – GlobalSearch Component Tests (Module 17)
 * Tests search input rendering, clear button, and result display.
 * Run with: npm test
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GlobalSearch from '../components/GlobalSearch';

const mockResults = [
  { id: 'S-001', type: 'task', title: 'Implement Auth', subtitle: 'PHX-101' },
  { id: 'S-002', type: 'project', title: 'Setup Redis', subtitle: 'Infrastructure' },
];

beforeEach(() => {
  localStorage.setItem('cb_access_token', 'mock_token_for_testing');
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ results: mockResults }),
    })
  );
});

describe('GlobalSearch Component', () => {
  it('renders search input with placeholder', () => {
    render(<GlobalSearch onNavigate={vi.fn()} />);
    const input = screen.getByPlaceholderText(/search/i);
    expect(input).toBeDefined();
  });

  it('input accepts text input', () => {
    render(<GlobalSearch onNavigate={vi.fn()} />);
    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: 'auth' } });
    expect(input.value).toBe('auth');
  });

  it('shows search results after typing and debounce', async () => {
    render(<GlobalSearch onNavigate={vi.fn()} />);
    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: 'Auth' } });

    await waitFor(() => {
      const results = screen.queryAllByText(/Implement Auth/i);
      expect(results.length).toBeGreaterThan(0);
    }, { timeout: 1000 });
  });

  it('clears input when clear button is clicked', async () => {
    render(<GlobalSearch onNavigate={vi.fn()} />);
    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: 'test query' } });

    const clearBtn = screen.getByLabelText(/clear search/i);
    fireEvent.click(clearBtn);
    expect(input.value).toBe('');
  });

  it('shows empty state for query with no results', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      })
    );

    render(<GlobalSearch onNavigate={vi.fn()} />);
    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: 'zzz_no_match_xyz' } });

    await waitFor(() => {
      const noResults = screen.getByText(/no results for/i);
      expect(noResults).toBeDefined();
    }, { timeout: 1000 });
  });
});
