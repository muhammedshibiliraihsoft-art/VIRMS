import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PerformanceChart } from '../PerformanceChart';

describe('monthly accounting chart', () => {
  it('shows unavailable when monthly data cannot be loaded', () => {
    render(<PerformanceChart points={null} isLoading={false} hasError />);
    expect(screen.getByText('Monthly Accounting data unavailable')).toBeInTheDocument();
  });
  it('shows a negative correction below the zero line', () => {
    const points = Array.from({ length: 8 }, (_, index) => ({ label: String(index), income: index === 0 ? -500 : 0, expense: 0 }));
    render(<PerformanceChart points={points} isLoading={false} hasError={false} />);
    const svg = screen.getByRole('img');
    const baseline = svg.querySelector('line[stroke="#9ca3af"]');
    const bar = svg.querySelector('rect[fill="var(--theme-primary)"]');
    expect(baseline).not.toBeNull();
    expect(bar).not.toBeNull();
    expect(bar?.getAttribute('y')).toBe(baseline?.getAttribute('y1'));
    expect(Number(bar?.getAttribute('height'))).toBeGreaterThan(0);
  });
});
