import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { RecentActivityTable } from '../RecentActivityTable';

it('does not display cached rows when the activity request fails', () => {
  render(<RecentActivityTable hasError activities={[{ id: '1', code: 'REF-1', title: 'Old activity', subtitle: 'Accounting', amount: 10, status: 'Recorded', statusVariant: 'info', date: '2026-01-01', type: 'accounting' }]} />);
  expect(screen.getByText('Accounting activity unavailable')).toBeInTheDocument();
  expect(screen.queryByText('Old activity')).not.toBeInTheDocument();
});
