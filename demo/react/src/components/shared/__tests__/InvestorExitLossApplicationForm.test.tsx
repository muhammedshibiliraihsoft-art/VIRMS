import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InvestorExitLossApplicationForm } from '../InvestorExitLossApplicationForm';

const mocks = vi.hoisted(() => ({ accounts: vi.fn(), branches: vi.fn(), apply: vi.fn() }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: mocks.accounts }));
vi.mock('../../../api/authApi', () => ({ authApi: { phase5Branches: mocks.branches } }));
vi.mock('../../../api/phase5Api', () => ({ phase5Api: { recordInvestorExitLossApplication: mocks.apply } }));

const company = '22222222-2222-4222-8222-222222222222';
const investor = '33333333-3333-4333-8333-333333333333';
const exit = '44444444-4444-4444-8444-444444444444';
const loss = '55555555-5555-4555-8555-555555555555';
const branch = '66666666-6666-4666-8666-666666666666';
const account = '77777777-7777-4777-8777-777777777777';

describe('InvestorExitLossApplicationForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.accounts.mockResolvedValue([{ id: account, label: 'Bank', is_active: true }]);
    mocks.branches.mockResolvedValue({ results: [{ id: branch, name: 'Central' }], next: null });
    mocks.apply.mockResolvedValue({ id: exit });
  });

  it('records an actual partial Loss receipt against the selected confirmed Loss', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn().mockResolvedValue(undefined);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={queryClient}><InvestorExitLossApplicationForm
      companyId={company} userId="11111111-1111-4111-8111-111111111111" investorId={investor} onSaved={onSaved}
      position={{ investor_id: investor, exit_request_id: exit, notice_deadline: '2027-02-19T00:00:00Z',
        principal_available: '500.00', residual_confirmed_loss: '125.00', vehicles: [], confirmed_positions: [],
        confirmed_losses: [{ loss_result_id: loss, vehicle_id: loss, label: 'KL 11 P 5050', amount: '125.00' }], blockers: [],
        settlement_order: ['PRINCIPAL', 'RESIDUAL_LOSS'], closure_implemented: false, source_version: 'a'.repeat(64) }}
    /></QueryClientProvider>);

    await user.selectOptions(await screen.findByLabelText('Exit Loss source'), 'DIRECT_RECEIPT');
    await user.selectOptions(await screen.findByLabelText('Exit Loss Branch'), branch);
    await user.selectOptions(await screen.findByLabelText('Exit Loss Cash / Bank account'), account);
    await user.type(screen.getByLabelText('Exit Loss amount'), '50.00');
    await user.type(screen.getByLabelText('Exit Loss reason'), 'Receipt part of confirmed Loss');
    await user.click(screen.getByRole('button', { name: 'Record Loss application' }));

    await waitFor(() => expect(mocks.apply).toHaveBeenCalledWith(company, '11111111-1111-4111-8111-111111111111', investor, exit, {
      loss_result_id: loss, branch_id: branch, account_id: account, source: 'DIRECT_RECEIPT', amount: '50.00',
      effective_at: expect.any(String), expected_source_version: 'a'.repeat(64), reason: 'Receipt part of confirmed Loss',
    }));
    expect(onSaved).toHaveBeenCalledOnce();
  });
});
