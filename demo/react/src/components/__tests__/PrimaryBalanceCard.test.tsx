import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { PrimaryBalanceCard } from '../PrimaryBalanceCard';

it('hides cached account details when the request fails', () => {
  render(<PrimaryBalanceCard accounts={[{ id: '1', label: 'Old bank', account_type: 'BANK', is_active: true, current_balance: '100.00' }]} isLoading={false} hasError onRecordReceipt={() => {}} onNewSale={() => {}} />);
  expect(screen.queryByText('Old bank')).not.toBeInTheDocument();
  expect(screen.getByText('Accounts unavailable')).toBeInTheDocument();
});
