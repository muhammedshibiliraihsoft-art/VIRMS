import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Phase5WorkspaceView } from '../Phase5WorkspaceView';

const ids = {
  user: '11111111-1111-4111-8111-111111111111',
  company: '22222222-2222-4222-8222-222222222222',
  branch: '33333333-3333-4333-8333-333333333333',
  vehicle: '44444444-4444-4444-8444-444444444444',
};

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useCompanyModuleStates: vi.fn(),
  hasCompanyBranchReadRole: vi.fn(),
  phase5Api: {
    vehicles: vi.fn(),
    purchases: vi.fn(),
    expenses: vi.fn(),
    sales: vi.fn(),
    sale: vi.fn(),
    investors: vi.fn(),
    fundCredits: vi.fn(),
    fundSummary: vi.fn(),
    principalReturns: vi.fn(),
    paymentAccountPreference: vi.fn(),
  },
  phase5Mutation: vi.fn(),
  accountingAccounts: vi.fn(),
  accountingCategories: vi.fn(),
  branches: vi.fn(),
}));

vi.mock('../../../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../../../api/queries', () => ({
  useCompanyModuleStates: mocks.useCompanyModuleStates,
  hasCompanyBranchReadRole: mocks.hasCompanyBranchReadRole,
}));
vi.mock('../../../api/authApi', () => ({ authApi: { phase5Branches: mocks.branches } }));
vi.mock('../../../api/accountingApi', () => ({
  accountingAccounts: mocks.accountingAccounts,
  accountingCategories: mocks.accountingCategories,
}));
vi.mock('../../../api/phase5Api', () => ({ phase5Api: mocks.phase5Api, phase5Mutation: mocks.phase5Mutation }));

const branch = { id: ids.branch, tenant_id: ids.company, name: 'Central' };
const baseVehicles = {
  count: 1,
  next: null,
  previous: null,
  results: [{
    id: ids.vehicle,
    company_id: ids.company,
    branch_id: ids.branch,
    branch_name: 'Central',
    registration: 'KL 11 P 5050',
    model: 'Hatchback',
    is_active: true,
    is_sold: false,
    sale_id: null,
  }],
};

function renderView(routeKey: 'Stock / Investor' | 'Investor Fund' | 'Running Capital' = 'Stock / Investor') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <Phase5WorkspaceView routeKey={routeKey} />
    </QueryClientProvider>,
  );
  return queryClient;
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.useAuth.mockReturnValue({
    status: 'authenticated',
    user: { id: ids.user, companies: [{ id: ids.company, roles: ['accountant'] }], company_context_truncated: false },
    currentCompany: {
      id: ids.company,
      branches: [branch],
      branches_truncated: false,
      company_wide_roles: ['accountant'],
    },
  });
  mocks.useCompanyModuleStates.mockReturnValue({
    data: { modules: [
      { code: 'vehicle_management', state: 'enabled' },
      { code: 'investment', state: 'enabled' },
      { code: 'accounting', state: 'enabled' },
    ] },
    isLoading: false,
  });
  mocks.hasCompanyBranchReadRole.mockReturnValue(true);
  mocks.phase5Api.vehicles.mockResolvedValue(baseVehicles);
  mocks.phase5Api.purchases.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.phase5Api.expenses.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.phase5Api.sales.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.phase5Api.investors.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.phase5Api.fundCredits.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.phase5Api.fundSummary.mockResolvedValue({
    company_id: ids.company, investor_id: null, branch_id: null,
    credit_total: '0.00', principal_return_total: '0.00', available_amount: '0.00',
  });
  mocks.phase5Api.principalReturns.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.phase5Api.paymentAccountPreference.mockResolvedValue({ company_id: ids.company, account_id: null, account_label: null });
  mocks.accountingAccounts.mockResolvedValue([]);
  mocks.accountingCategories.mockResolvedValue([]);
  mocks.branches.mockResolvedValue({ results: [branch], next: null });
});

describe('Phase 5 Vehicle API workspace', () => {
  it('allows a no-prior-payment refund after explicitly classifying its excess as new Income', async () => {
    const user = userEvent.setup();
    const expenseId = '55555555-5555-4555-8555-555555555555';
    const incomeCategoryId = '77777777-7777-4777-8777-777777777777';
    mocks.phase5Api.expenses.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: expenseId,
        vehicle_id: ids.vehicle,
        company_id: ids.company,
        branch_id: ids.branch,
        amount: '5000.00',
        description: 'Brake repair',
        investor_id: null,
        investor_fund_amount: '0.00',
        running_capital_amount: '5000.00',
        paid_total: '0.00',
        applied_refund_total: '0.00',
        net_paid: '0.00',
        payable: '5000.00',
        effective_at: '2026-11-01T00:00:00Z',
        payments: [],
        refunds: [],
      }],
    });
    mocks.accountingAccounts.mockResolvedValue([{
      id: '88888888-8888-4888-8888-888888888888',
      account_type: 'BANK',
      label: 'Main Bank',
      is_active: true,
    }]);
    mocks.accountingCategories.mockResolvedValue([{
      id: incomeCategoryId,
      kind: 'INCOME',
      label: 'Workshop refund income',
      is_active: true,
    }]);
    mocks.phase5Mutation.mockResolvedValue({ id: '99999999-9999-4999-8999-999999999999' });
    renderView();

    await user.click(await screen.findByRole('button', { name: 'Open' }));
    await user.click(await screen.findByRole('button', { name: 'Refund' }));
    await user.selectOptions(await screen.findByLabelText(/Cash \/ Bank account/), '88888888-8888-4888-8888-888888888888');
    await user.type(screen.getByLabelText(/Actual refund received/), '500');
    await user.selectOptions(await screen.findByLabelText(/New Company Income category/), incomeCategoryId);
    await user.type(screen.getByLabelText(/New Income description/), 'Workshop returned more than paid');
    expect(await screen.findByRole('status')).toHaveTextContent(/recorded as a new Company Income entry/);
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(mocks.phase5Mutation).toHaveBeenCalled());
    expect(mocks.phase5Mutation.mock.calls[0]?.[3]).toBe(`expenses/${expenseId}/refunds/`);
    expect(mocks.phase5Mutation.mock.calls[0]?.[4]).toMatchObject({
      amount: '500',
      excess_income_category_id: incomeCategoryId,
      excess_income_description: 'Workshop returned more than paid',
    });
  });

  it('loads Company Branches for a Company Accountant without assigned-Branch summaries', async () => {
    const user = userEvent.setup();
    mocks.useAuth.mockReturnValue({ status: 'authenticated', user: { id: ids.user }, currentCompany: { id: ids.company, branches: [], branches_truncated: false, company_wide_roles: ['accountant'] } });
    mocks.phase5Api.investors.mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', company_id: ids.company, name: 'Investor', is_active: true }] });
    renderView('Investor Fund');
    await user.click(await screen.findByRole('button', { name: 'Fund Credit' }));
    expect(await screen.findByRole('option', { name: 'Central' })).toBeInTheDocument();
    expect(mocks.branches).toHaveBeenCalled();
  });
  it('shows the backend total across expense pages instead of the visible page subtotal', async () => {
    const user = userEvent.setup();
    const expense = { id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd', description: 'Repair', amount: '100.00', investor_fund_amount: '0.00', running_capital_amount: '100.00', paid_total: '0.00', payable: '100.00', net_paid: '0.00' };
    mocks.phase5Api.expenses.mockImplementation(async (_company: string, _vehicle: string, options: { page: number }) => ({
      count: 21, next: options.page === 1 ? '?page=2' : null, previous: options.page === 1 ? null : '?page=1',
      results: [expense], running_capital_total: '2150.00',
    }));
    renderView('Running Capital');
    await user.click(await screen.findByRole('button', { name: /KL 11 P 5050/ }));
    expect(await screen.findByText(/₹2,150\.00/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Next/ }));
    expect(await screen.findByText(/₹2,150\.00/)).toBeInTheDocument();
  });
  it('submits the Investor for a Fund-first vehicle expense without inventing a source split', async () => {
    const user = userEvent.setup();
    const investor = { id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', company_id: ids.company, name: 'Fund Investor', is_active: true };
    mocks.phase5Api.investors.mockResolvedValue({ count: 1, next: null, previous: null, results: [investor] });
    mocks.phase5Mutation.mockResolvedValue({ id: '77777777-7777-4777-8777-777777777777' });
    renderView();
    await user.click(await screen.findByRole('button', { name: 'Open' }));
    await user.click(await screen.findByRole('button', { name: 'Add expense' }));
    await user.type(screen.getByLabelText('Total vehicle expense *'), '5000');
    await user.type(screen.getByLabelText('Expense description *'), 'Repair');
    await user.selectOptions(await screen.findByLabelText(/^Investor/), investor.id);
    await user.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(mocks.phase5Mutation).toHaveBeenCalled());
    const body = mocks.phase5Mutation.mock.calls[0][4] as Record<string, unknown>;
    expect(body.investor_id).toBe(investor.id);
    expect(body).not.toHaveProperty('investor_fund_amount');
    expect(body).not.toHaveProperty('running_capital_amount');
  });
  it('loads Investor choices beyond the first page', async () => {
    const first = { id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', company_id: ids.company, name: 'First Investor', is_active: true };
    const later = { id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', company_id: ids.company, name: 'Later Investor', is_active: true };
    mocks.phase5Api.investors.mockImplementation(async (_company: string, page: number) => page === 1
      ? { count: 2, next: '?page=2', previous: null, results: [first] }
      : { count: 2, next: null, previous: '?page=1', results: [later] });
    renderView('Investor Fund');
    expect(await screen.findByText('Later Investor', { selector: 'div' })).toBeInTheDocument();
    expect(mocks.phase5Api.investors).toHaveBeenCalledWith(ids.company, 2, expect.any(AbortSignal));
  });
  it('keeps the mutation form open and shows the server error without showing success', async () => {
    const user = userEvent.setup();
    mocks.phase5Mutation.mockRejectedValue(new Error('Vehicle Management is OFF.'));
    renderView();

    await user.click(await screen.findByRole('button', { name: 'Register Vehicle' }));
    await user.type(screen.getByLabelText('Registration *'), 'KL 11 P 7070');
    await user.type(screen.getByLabelText('Model / description *'), 'Sedan');
    await user.selectOptions(screen.getByLabelText('Branch *'), ids.branch);
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Vehicle Management is OFF.');
    expect(screen.getByRole('heading', { name: 'Register stock vehicle' })).toBeInTheDocument();
    expect(screen.queryByText('Saved successfully. The latest server records are refreshing.')).not.toBeInTheDocument();
  });

  it('refreshes the backend list only after the mutation succeeds', async () => {
    const user = userEvent.setup();
    let rows = baseVehicles.results;
    mocks.phase5Api.vehicles.mockImplementation(async () => ({ ...baseVehicles, count: rows.length, results: rows }));
    mocks.phase5Mutation.mockImplementation(async (_companyId: string, _userId: string, _module: string, suffix: string, body: Record<string, unknown>) => {
      expect(suffix).toBe('vehicles/');
      rows = [...rows, {
        id: '66666666-6666-4666-8666-666666666666',
        company_id: ids.company,
        branch_id: ids.branch,
        branch_name: 'Central',
        registration: String(body.registration),
        model: String(body.model),
        is_active: true,
        is_sold: false,
        sale_id: null,
      }];
      return { id: '66666666-6666-4666-8666-666666666666' };
    });
    renderView();

    await user.click(await screen.findByRole('button', { name: 'Register Vehicle' }));
    await user.type(screen.getByLabelText('Registration *'), 'KL 11 P 7070');
    await user.type(screen.getByLabelText('Model / description *'), 'Sedan');
    await user.selectOptions(screen.getByLabelText('Branch *'), ids.branch);
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(await screen.findByText('KL 11 P 7070')).toBeInTheDocument();
    expect(await screen.findByText('Saved successfully. The latest server records are refreshing.')).toBeInTheDocument();
  });

  it('sends the selected historical Sale date to the backend', async () => {
    const user = userEvent.setup();
    mocks.phase5Api.purchases.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: '55555555-5555-4555-8555-555555555555',
        vehicle_id: ids.vehicle,
        company_id: ids.company,
        branch_id: ids.branch,
        purchase_cost: '500000.00',
        seller_name: 'Seller',
        seller_phone: '',
        investor_id: null,
        investor_fund_amount: '0.00',
        running_capital_amount: '500000.00',
        seller_paid: '0.00',
        seller_payable: '500000.00',
        no_advance_warning: true,
        purchased_at: '2026-01-01T00:00:00Z',
        payments: [],
        refunds: [],
        correction_version: 0,
      }],
    });
    mocks.phase5Mutation.mockResolvedValue({ id: '77777777-7777-4777-8777-777777777777' });
    renderView();

    await user.click(await screen.findByRole('button', { name: 'Open' }));
    await user.click(await screen.findByRole('button', { name: 'Confirm Sale' }));
    await user.type(screen.getByLabelText('Sale price *'), '600000.00');
    await user.type(screen.getByLabelText('Buyer name *'), 'Buyer');
    await user.type(screen.getByLabelText('Buyer phone *'), '9876543210');
    const saleDate = screen.getByLabelText('Sale date and time');
    fireEvent.change(saleDate, { target: { value: '2026-10-01T11:30' } });
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(mocks.phase5Mutation).toHaveBeenCalled());
    const requestBody = mocks.phase5Mutation.mock.calls[0][4] as Record<string, unknown>;
    expect(requestBody.sold_at).toBe(new Date('2026-10-01T11:30').toISOString());
  });

  it('lets an Accountant correct a Fund Credit and warns when linked history needs manual review', async () => {
    const user = userEvent.setup();
    const originalInvestor = { id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', company_id: ids.company, name: 'Original Investor', is_active: true };
    const correctedInvestor = { id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', company_id: ids.company, name: 'Correct Investor', is_active: true };
    mocks.phase5Api.investors.mockResolvedValue({ count: 2, next: null, previous: null, results: [originalInvestor, correctedInvestor] });
    mocks.phase5Api.fundCredits.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
        investor_id: originalInvestor.id,
        original_investor_id: '99999999-9999-4999-8999-999999999999',
        branch_id: ids.branch,
        amount: '50000.00',
        reference: 'BANK-REFERENCE-1',
        effective_at: '2026-10-01T00:00:00Z',
        recorded_at: '2026-10-01T00:00:00Z',
        accounting_event_id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
        correction_version: 1,
        manual_review_required: true,
        attribution_corrections: [{
          id: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
          from_investor_id: '99999999-9999-4999-8999-999999999999',
          to_investor_id: originalInvestor.id,
          amount: '50000.00',
          effective_at: '2026-10-01T00:00:00Z',
          recorded_at: '2026-11-10T00:00:00Z',
          reason: 'Earlier attribution correction.',
        }],
      }],
    });
    mocks.phase5Mutation.mockResolvedValue({ id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc' });
    renderView('Investor Fund');

    await user.click(await screen.findByRole('button', { name: 'Correct Investor' }));
    expect(screen.getByRole('status')).toHaveTextContent('Accountant review is required');
    await user.selectOptions(screen.getByLabelText('Correct Investor *'), correctedInvestor.id);
    await user.type(screen.getByLabelText('Correction reason *'), 'The transfer was assigned to the wrong Investor.');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(mocks.phase5Mutation).toHaveBeenCalled());
    expect(mocks.phase5Mutation.mock.calls[0]?.[2]).toBe('investment');
    expect(mocks.phase5Mutation.mock.calls[0]?.[3]).toBe('fund/credits/cccccccc-cccc-4ccc-8ccc-cccccccccccc/corrections/');
    expect(mocks.phase5Mutation.mock.calls[0]?.[4]).toEqual({
      to_investor_id: correctedInvestor.id,
      reason: 'The transfer was assigned to the wrong Investor.',
    });

  });
});
