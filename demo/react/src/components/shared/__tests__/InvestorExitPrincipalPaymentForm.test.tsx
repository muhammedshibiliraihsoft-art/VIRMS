import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InvestorExitPrincipalPaymentForm } from '../InvestorExitPrincipalPaymentForm';

const mocks = vi.hoisted(() => ({ accounts: vi.fn(), branches: vi.fn(), payment: vi.fn() }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: mocks.accounts }));
vi.mock('../../../api/authApi', () => ({ authApi: { phase5Branches: mocks.branches } }));
vi.mock('../../../api/phase5Api', () => ({ phase5Api: { recordInvestorExitPrincipalPayment: mocks.payment } }));

const company = '22222222-2222-4222-8222-222222222222';
const investor = '33333333-3333-4333-8333-333333333333';
const request = '44444444-4444-4444-8444-444444444444';
const branch = '55555555-5555-4555-8555-555555555555';
const account = '66666666-6666-4666-8666-666666666666';

describe('InvestorExitPrincipalPaymentForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.accounts.mockResolvedValue([{ id: account, label: 'Bank', is_active: true }]);
    mocks.branches.mockResolvedValue({ results: [{ id: branch, name: 'Central' }], next: null });
    mocks.payment.mockResolvedValue({ id: request });
  });

  it('submits the reviewed version and refreshes the current settlement after payment', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn().mockResolvedValue(undefined);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={queryClient}><InvestorExitPrincipalPaymentForm
      companyId={company} userId="11111111-1111-4111-8111-111111111111" investorId={investor} onSaved={onSaved}
      position={{ investor_id: investor, exit_request_id: request, notice_deadline: '2027-02-19T00:00:00Z',
        principal_available: '900.00', residual_confirmed_loss: '0.00', vehicles: [], confirmed_positions: [], confirmed_losses: [],
        blockers: [], settlement_order: ['PRINCIPAL'], closure_implemented: false, source_version: 'a'.repeat(64) }}
    /></QueryClientProvider>);

    await user.selectOptions(await screen.findByLabelText('Exit payment Branch'), branch);
    await user.selectOptions(screen.getByLabelText('Exit payment Cash / Bank account'), account);
    await user.type(screen.getByLabelText('Exit principal amount'), '250.00');
    await user.type(screen.getByLabelText('Exit payment reference'), 'Receipt 123');
    fireEvent.change(screen.getByLabelText('Exit payment date'), { target: { value: '2026-11-19T10:00' } });
    await user.type(screen.getByLabelText('Exit payment reason'), 'Partial principal payment');
    await user.click(screen.getByRole('button', { name: 'Record partial payment' }));

    await waitFor(() => expect(mocks.payment).toHaveBeenCalledWith(company, '11111111-1111-4111-8111-111111111111', investor, request, {
      branch_id: branch, account_id: account, amount: '250.00', reference: 'Receipt 123', effective_at: new Date('2026-11-19T10:00').toISOString(),
      expected_source_version: 'a'.repeat(64), reason: 'Partial principal payment',
    }));
    expect(onSaved).toHaveBeenCalledOnce();
  });
});
