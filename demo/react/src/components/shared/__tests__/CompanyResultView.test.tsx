import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CompanyResultView } from '../CompanyResultView';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useAccountingAccounts: vi.fn(),
  useAccountingBranches: vi.fn(),
  useAccountingResult: vi.fn(),
  companyPeriodConfirmations: vi.fn(),
  confirmCompanyPeriod: vi.fn(),
}));

vi.mock('../../../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../../../api/accountingQueries', () => ({
  useAccountingAccounts: mocks.useAccountingAccounts,
  useAccountingBranches: mocks.useAccountingBranches,
  useAccountingResult: mocks.useAccountingResult,
}));
vi.mock('../../../api/accountingApi', async (importOriginal) => ({
  ...await importOriginal<typeof import('../../../api/accountingApi')>(),
  companyPeriodConfirmations: mocks.companyPeriodConfirmations,
  confirmCompanyPeriod: mocks.confirmCompanyPeriod,
}));

const companyId = '22222222-2222-4222-8222-222222222222';
const branchId = '33333333-3333-4333-8333-333333333333';

beforeEach(() => {
  vi.clearAllMocks();
  mocks.useAuth.mockReturnValue({
    user: { id: '11111111-1111-4111-8111-111111111111' },
    currentCompany: { id: companyId, company_wide_roles: ['accountant'] },
  });
  mocks.useAccountingBranches.mockReturnValue({ data: [{ id: branchId, name: 'Central' }], isPending: false, isError: false });
  mocks.useAccountingAccounts.mockReturnValue({ data: [], isPending: false, isError: false });
  mocks.useAccountingResult.mockReturnValue({
    data: {
      period: 'annual', year: 2026, month: null, branch_id: null,
      period_start: '2026-01-01', period_end: '2027-01-01', timezone: 'Asia/Kolkata', starts_at: '2025-12-31T18:30:00Z', ends_before: '2026-12-31T18:30:00Z',
      income_amount: '100000.00', expense_amount: '25000.00', accounting_result_amount: '75000.00', source_version: 'a'.repeat(64),
      income_event_count: 0, expense_event_count: 0, actual_receipts_amount: '0.00', actual_payments_amount: '0.00',
      transaction_event_count: 0, cash_inflow_amount: '0.00', cash_outflow_amount: '0.00', net_movement_amount: '0.00',
      corrected_event_count: 0, reversal_event_count: 0, reallocation_event_count: 0,
      currency: 'INR', scope: 'recorded_accounting_events',
    },
    isPending: false, isError: false,
  });
  mocks.companyPeriodConfirmations.mockResolvedValue({ confirmations: [], history: [] });
  mocks.confirmCompanyPeriod.mockResolvedValue({ id: '55555555-5555-4555-8555-555555555555' });
});

function renderView() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(<QueryClientProvider client={client}><CompanyResultView /></QueryClientProvider>);
}

describe('CompanyResultView', () => {
  it('shows the API-backed Accounting Result with its limited meaning', () => {
    renderView();

    expect(screen.getByRole('heading', { name: 'Company Accounting Result' })).toBeInTheDocument();
    expect(screen.getByText('₹1,00,000.00')).toBeInTheDocument();
    expect(screen.getByText('₹25,000.00')).toBeInTheDocument();
    expect(screen.getAllByText('₹75,000.00')).toHaveLength(2);
    expect(screen.getByText(/not the final distributable Company Profit/)).toBeInTheDocument();
    expect(screen.getByText(/1 Jan 2026\s+through\s+1 Jan 2027/)).toBeInTheDocument();
    expect(screen.queryByText(/Inventory Margin Realized/)).not.toBeInTheDocument();
  });

  it('sends the selected period and Branch scope to the backend query', async () => {
    const user = userEvent.setup();
    mocks.useAuth.mockReturnValue({
      user: { id: '11111111-1111-4111-8111-111111111111' },
      currentCompany: { id: companyId, company_wide_roles: [] },
    });
    mocks.useAccountingBranches.mockReturnValue({ data: [{ id: branchId, name: 'Central' }, { id: '44444444-4444-4444-8444-444444444444', name: 'West' }], isPending: false, isError: false });
    renderView();

    await user.selectOptions(screen.getByLabelText('Result Branch'), branchId);
    await user.selectOptions(screen.getByLabelText('Reporting period'), 'h1');

    expect(mocks.useAccountingResult).toHaveBeenLastCalledWith(expect.objectContaining({
      period: 'h1', branchId,
    }));
  });

  it('lets the Company Accountant confirm a liability-reviewed amount without recording a payment', async () => {
    const user = userEvent.setup();
    renderView();
    await user.type(screen.getByLabelText('Confirmed distributable amount'), '50000.00');
    await user.type(screen.getByLabelText('Liability review reason'), 'Reviewed unpaid bills and obligations');
    await user.type(screen.getByLabelText('Company period confirmation reason'), 'Confirmed after liability review');
    await user.click(screen.getByRole('button', { name: 'Confirm period amount' }));
    await vi.waitFor(() => expect(mocks.confirmCompanyPeriod).toHaveBeenCalledWith(companyId, '11111111-1111-4111-8111-111111111111', expect.objectContaining({
      period_type: 'annual', year: 2026, distributable_amount: '50000.00', liabilities_reviewed: true,
    })));
  });
});
