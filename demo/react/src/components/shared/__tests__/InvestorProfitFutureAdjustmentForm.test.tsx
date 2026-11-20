import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { InvestorProfitFutureAdjustmentForm } from '../InvestorProfitFutureAdjustmentForm';

const adjust = vi.hoisted(() => vi.fn());
vi.mock('../../../api/phase5Api', () => ({ phase5Api: { adjustInvestorRecoverableAgainstProfit: adjust } }));

it('submits only an explicitly selected future Profit source and amount', async () => {
  const user = userEvent.setup();
  const close = vi.fn();
  adjust.mockResolvedValue({ id: 'adjustment' });
  const client = new QueryClient();
  render(<QueryClientProvider client={client}><InvestorProfitFutureAdjustmentForm
    companyId="company" userId="accountant" investorId="investor" onClose={close}
    position={{ id: 'debt', source_version: 'a'.repeat(64), kind: 'RECOVERABLE', amount: '1000.00',
      is_current: true, confirmed_at: '2026-11-19', reason: 'Confirmed' }}
    targets={[{ profit_position_id: 'future-position', profit_result_id: 'future-result',
      source_version: 'b'.repeat(64), amount: '700.00', label: 'KL 11 P 5921' }]} /></QueryClientProvider>);
  expect(adjust).not.toHaveBeenCalled();
  await user.selectOptions(screen.getByLabelText('Future Profit source'), 'future-result');
  await user.type(screen.getByLabelText('Future adjustment amount'), '400.00');
  await user.type(screen.getByLabelText('Future adjustment reason'), 'Apply confirmed future Profit');
  await user.click(screen.getByRole('button', { name: 'Confirm adjustment' }));
  await waitFor(() => expect(adjust).toHaveBeenCalledWith('company', 'accountant', 'investor', 'debt', {
    profit_position_id: 'future-position', profit_result_id: 'future-result', amount: '400.00',
    expected_source_version: 'a'.repeat(64), expected_profit_source_version: 'b'.repeat(64),
    reason: 'Apply confirmed future Profit',
  }));
  await waitFor(() => expect(close).toHaveBeenCalledOnce());
});
