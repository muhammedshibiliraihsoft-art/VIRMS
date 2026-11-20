import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { InvestorProfitRepaymentForm } from '../InvestorProfitRepaymentForm';

const calls = vi.hoisted(() => ({ accounts: vi.fn(), branches: vi.fn(), receive: vi.fn() }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: calls.accounts }));
vi.mock('../../../api/authApi', () => ({ authApi: { phase5Branches: calls.branches } }));
vi.mock('../../../api/phase5Api', () => ({ phase5Api: { receiveInvestorProfitRepayment: calls.receive } }));

const company = '11111111-1111-4111-8111-111111111111';
const investor = '22222222-2222-4222-8222-222222222222';
const account = '33333333-3333-4333-8333-333333333333';
const branch = '44444444-4444-4444-8444-444444444444';
const position = { id: '55555555-5555-4555-8555-555555555555', kind: 'RECOVERABLE' as const,
  amount: '1000.00', source_version: 'a'.repeat(64), is_current: true, confirmed_at: '2026-11-19', reason: 'Confirmed' };

beforeEach(() => {
  vi.resetAllMocks();
  calls.accounts.mockResolvedValue([{ id: account, label: 'Main Bank', is_active: true }]);
  calls.branches.mockResolvedValue({ results: [{ id: branch, name: 'Central' }], next: null });
});

it('records a partial actual repayment and closes after refreshing the position', async () => {
  const user = userEvent.setup();
  const close = vi.fn();
  calls.receive.mockResolvedValue({ receipt_id: account });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><InvestorProfitRepaymentForm companyId={company} userId={company}
    investorId={investor} position={position} onClose={close} /></QueryClientProvider>);
  await user.selectOptions(await screen.findByLabelText('Repayment Branch'), branch);
  await user.selectOptions(screen.getByLabelText('Repayment Cash / Bank account'), account);
  await user.type(screen.getByLabelText('Actual repayment amount'), '400.00');
  await user.type(screen.getByLabelText('Repayment reason'), 'Bank receipt confirmed');
  await user.click(screen.getByRole('button', { name: 'Record receipt' }));
  await waitFor(() => expect(calls.receive).toHaveBeenCalledWith(company, company, investor, position.id, {
    branch_id: branch, account_id: account, amount: '400.00', reason: 'Bank receipt confirmed',
    expected_source_version: 'a'.repeat(64),
  }));
  await waitFor(() => expect(close).toHaveBeenCalledTimes(1));
});
