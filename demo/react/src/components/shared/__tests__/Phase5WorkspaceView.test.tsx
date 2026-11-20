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
  sale: '55555555-5555-4555-8555-555555555555',
  investor: '88888888-8888-4888-8888-888888888888',
  account: '99999999-9999-4999-8999-999999999999',
  result: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
};

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useCompanyModuleStates: vi.fn(),
  hasCompanyBranchReadRole: vi.fn(),
  phase5Api: {
    vehicles: vi.fn(),
    vehicleFinancialPosition: vi.fn(),
    purchases: vi.fn(),
    expenses: vi.fn(),
    sales: vi.fn(),
    sale: vi.fn(),
    investors: vi.fn(),
    fundCredits: vi.fn(),
    fundSummary: vi.fn(),
    principalReturns: vi.fn(),
    profitCalendarConfigurations: vi.fn(),
    configureProfitCalendar: vi.fn(),
    paymentAccountPreference: vi.fn(),
    confirmVehicleResult: vi.fn(),
    recordInvestorVehicleProfitPayment: vi.fn(),
    investorProfitLossOffsetOptions: vi.fn(),
    recordInvestorProfitLossOffset: vi.fn(),
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

function renderView(routeKey: 'Stock / Investor' | 'Investor Fund' | 'Running Capital' | 'Vehicle Sales' | 'Collections' | 'Sale Corrections & Refunds' = 'Stock / Investor') {
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
      roles: ['accountant'],
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
  mocks.phase5Api.vehicleFinancialPosition.mockResolvedValue({
    vehicle_id: ids.vehicle, company_id: ids.company, branch_id: ids.branch,
    purchase_id: '55555555-5555-4555-8555-555555555555', sale_id: '66666666-6666-4666-8666-666666666666',
    purchase_cost: '100000.00', vehicle_expense_cost: '5000.00', total_vehicle_cost: '105000.00',
    investor_fund_cost: '70000.00', running_capital_cost: '35000.00', sale_price: '120000.00',
    actual_net_collection: '80000.00', buyer_receivable: '40000.00', buyer_refund_payable: '0.00',
    calculated_result: '15000.00', status: 'PROVISIONAL_COLLECTION', settlement_eligible: false,
    source_version: 'a'.repeat(64), confirmed_result: null,
    purchase_correction_version: 0, expense_correction_versions: [], sale_correction_version: 0,
  });
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
  mocks.phase5Api.profitCalendarConfigurations.mockResolvedValue([]);
  mocks.phase5Api.configureProfitCalendar.mockResolvedValue({
    id: 'ffffffff-ffff-4fff-8fff-ffffffffffff', investor_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    effective_start: '2026-11-19', duration_months: 6, version: 1,
    recorded_at: '2026-11-19T00:00:00Z', actor_id: ids.user,
  });
  mocks.accountingAccounts.mockResolvedValue([]);
  mocks.accountingCategories.mockResolvedValue([]);
  mocks.branches.mockResolvedValue({ results: [branch], next: null });
});

describe('Phase 5 Vehicle API workspace', () => {
  it('blocks result confirmation when the Investor agreement needs review', async () => {
    const user = userEvent.setup();
    mocks.phase5Api.vehicleFinancialPosition.mockResolvedValue({
      vehicle_id: ids.vehicle, company_id: ids.company, branch_id: ids.branch,
      purchase_id: ids.sale, sale_id: ids.sale, investor_id: null, investor_share_agreement_id: null,
      investor_share_percentage_snapshot: null, profit_share_status: 'AGREEMENT_SNAPSHOT_MISSING',
      purchase_cost: '10000.00', vehicle_expense_cost: '1000.00', total_vehicle_cost: '11000.00',
      investor_fund_cost: '1000.00', running_capital_cost: '10000.00', sale_price: '12000.00',
      actual_net_collection: '12000.00', buyer_receivable: '0.00', buyer_refund_payable: '0.00',
      calculated_result: '1000.00', status: 'READY_FOR_REVIEW', settlement_eligible: false,
      suggested_loss_split: null, source_version: 'a'.repeat(64), confirmed_result: null,
      purchase_correction_version: 0, expense_correction_versions: [], sale_correction_version: 0,
    });
    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: /KL 11 P 5050/ }));
    expect(await screen.findByText(/No matching Investor share agreement snapshot/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Confirm result' })).not.toBeInTheDocument();
    expect(mocks.phase5Api.confirmVehicleResult).not.toHaveBeenCalled();
  });

  it('shows a backend-derived provisional vehicle position without claiming settlement', async () => {
    const user = userEvent.setup();
    renderView('Stock / Investor');

    await user.click(await screen.findByRole('button', { name: /KL 11 P 5050/ }));

    const panel = await screen.findByRole('region', { name: 'Vehicle financial position' });
    expect(panel).toHaveTextContent('Current vehicle position');
    expect(panel).toHaveTextContent('Collection in progress');
    expect(panel).toHaveTextContent('Total cost');
    expect(panel).toHaveTextContent('1,05,000.00');
    expect(panel).toHaveTextContent('Calculated result');
    expect(panel).toHaveTextContent('15,000.00');
    expect(panel).toHaveTextContent('does not post cash or mark any amount Paid');
  });

  it('shows the suggested Loss split as a calculation before confirmation', async () => {
    const user = userEvent.setup();
    mocks.phase5Api.vehicleFinancialPosition.mockResolvedValue({
      vehicle_id: ids.vehicle, company_id: ids.company, branch_id: ids.branch,
      purchase_id: '55555555-5555-4555-8555-555555555555', sale_id: ids.sale,
      investor_id: ids.investor, investor_share_agreement_id: null,
      investor_share_percentage_snapshot: '40.0000', profit_share_status: 'AVAILABLE',
      purchase_cost: '10000.00', vehicle_expense_cost: '0.00', total_vehicle_cost: '10000.00',
      investor_fund_cost: '6000.00', running_capital_cost: '4000.00', sale_price: '8000.00',
      actual_net_collection: '8000.00', buyer_receivable: '0.00', buyer_refund_payable: '0.00',
      calculated_result: '-2000.00', status: 'LOSS_REVIEW_REQUIRED', settlement_eligible: false,
      suggested_loss_split: { investor_loss: '800.00', company_loss: '1200.00' },
      source_version: 'a'.repeat(64), confirmed_result: null,
      purchase_correction_version: 0, expense_correction_versions: [], sale_correction_version: 0,
    });
    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: /KL 11 P 5050/ }));
    const suggestion = await screen.findByText(/Suggested Loss for review/);
    expect(suggestion).toHaveTextContent('800.00');
    expect(suggestion).toHaveTextContent('1,200.00');
    expect(suggestion).toHaveTextContent('not a confirmed Loss or Fund deduction');
    expect(mocks.phase5Api.confirmVehicleResult).not.toHaveBeenCalled();
  });

  it('lets the Company Accountant edit Loss impacts before confirmation', async () => {
    const user = userEvent.setup();
    mocks.phase5Api.vehicleFinancialPosition.mockResolvedValue({
      vehicle_id: ids.vehicle, company_id: ids.company, branch_id: ids.branch,
      purchase_id: ids.sale, sale_id: ids.sale, investor_id: ids.investor, investor_share_agreement_id: null,
      investor_share_percentage_snapshot: '40.0000', profit_share_status: 'AVAILABLE',
      purchase_cost: '10000.00', vehicle_expense_cost: '0.00', total_vehicle_cost: '10000.00',
      investor_fund_cost: '6000.00', running_capital_cost: '4000.00', sale_price: '8000.00',
      actual_net_collection: '8000.00', buyer_receivable: '0.00', buyer_refund_payable: '0.00',
      calculated_result: '-2000.00', status: 'LOSS_REVIEW_REQUIRED', settlement_eligible: false,
      suggested_loss_split: { investor_loss: '800.00', company_loss: '1200.00' },
      source_version: 'a'.repeat(64), confirmed_result: null,
      purchase_correction_version: 0, expense_correction_versions: [], sale_correction_version: 0,
    });
    mocks.phase5Api.confirmVehicleResult.mockResolvedValue({ id: ids.result });
    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: /KL 11 P 5050/ }));
    const investorLoss = await screen.findByLabelText('Investor Loss amount');
    const companyLoss = screen.getByLabelText('Company Loss amount');
    await user.type(screen.getByLabelText('Accountant review note'), 'Reviewed Loss impact');
    await user.clear(investorLoss);
    await user.type(investorLoss, '600.00');
    expect(screen.getByRole('button', { name: 'Confirm reviewed Loss' })).toBeDisabled();
    await user.clear(companyLoss);
    await user.type(companyLoss, '1400.00');
    await user.click(screen.getByRole('button', { name: 'Confirm reviewed Loss' }));
    await waitFor(() => expect(mocks.phase5Api.confirmVehicleResult).toHaveBeenCalledWith(
      ids.company, ids.user, ids.vehicle, { expected_source_version: 'a'.repeat(64),
        reason: 'Reviewed Loss impact', investor_loss_amount: '600.00', company_loss_amount: '1400.00' },
    ));
  });

  it('requires a reason and refreshes the source-backed result after Accountant confirmation', async () => {
    const user = userEvent.setup();
    const confirmedResult = {
      id: '77777777-7777-4777-8777-777777777777', version: 1,
      source_version: 'b'.repeat(64), is_current: true, result_kind: 'PROFIT',
      result_amount: '15000.00', investor_share_amount: '4950.00', company_share_amount: '10050.00',
      investor_profit_paid: '0.00', investor_profit_remaining: '4950.00', investor_profit_overpaid: '0.00',
      confirmed_at: '2026-11-19T00:00:00Z', reason: 'Checked source records',
    };
    let confirmed = false;
    mocks.phase5Api.vehicleFinancialPosition.mockImplementation(async () => ({
      ...{
        vehicle_id: ids.vehicle, company_id: ids.company, branch_id: ids.branch,
        purchase_id: '55555555-5555-4555-8555-555555555555', sale_id: null,
        investor_id: '88888888-8888-4888-8888-888888888888', investor_share_agreement_id: null,
        investor_share_percentage_snapshot: '33.0000', profit_share_status: 'AVAILABLE',
        purchase_cost: '100000.00', vehicle_expense_cost: '5000.00', total_vehicle_cost: '105000.00',
        investor_fund_cost: '70000.00', running_capital_cost: '35000.00', sale_price: null,
        actual_net_collection: '120000.00', buyer_receivable: null, buyer_refund_payable: null,
        calculated_result: '15000.00', status: 'READY_FOR_REVIEW', settlement_eligible: false,
        source_version: 'a'.repeat(64), purchase_correction_version: 0,
        expense_correction_versions: [], sale_correction_version: 0,
      },
      confirmed_result: confirmed ? confirmedResult : null,
    }));
    mocks.phase5Api.confirmVehicleResult.mockImplementation(async () => {
      confirmed = true;
      return confirmedResult;
    });
    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: /KL 11 P 5050/ }));
    const confirm = await screen.findByRole('button', { name: 'Confirm result' });
    expect(confirm).toBeDisabled();
    await user.type(screen.getByLabelText('Accountant review note'), 'Checked source records');
    await user.click(confirm);
    await waitFor(() => expect(mocks.phase5Api.confirmVehicleResult).toHaveBeenCalledWith(
      ids.company, ids.user, ids.vehicle,
      { expected_source_version: 'a'.repeat(64), reason: 'Checked source records' },
    ));
    expect(await screen.findByText(/Accountant-confirmed result/)).toBeInTheDocument();
  });

  it('requires explicit Accountant principal refund obligation and sends the reviewed source', async () => {
    const user = userEvent.setup();
    const current = await mocks.phase5Api.vehicleFinancialPosition();
    mocks.phase5Api.vehicleFinancialPosition.mockResolvedValue({
      ...current, buyer_refund_payable: '5000.00', status: 'REFUND_PENDING',
    });
    mocks.phase5Mutation.mockResolvedValueOnce({ id: ids.result });
    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: 'Open' }));
    await user.click(screen.getByRole('button', { name: 'Confirm principal refund obligation' }));
    await user.type(screen.getByLabelText(/Total outstanding Investor principal refund/), '2000.00');
    await user.type(screen.getByLabelText(/Refund obligation confirmation reason/), 'Reviewed principal component');
    await user.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(mocks.phase5Mutation).toHaveBeenCalledWith(
      ids.company, ids.user, 'investment', 'sales/66666666-6666-4666-8666-666666666666/principal-refund-reviews/',
      { expected_source_version: 'a'.repeat(64), principal_amount: '2000.00', reason: 'Reviewed principal component' }, 'POST',
    ));
  });

  it('submits recovery with the reviewed source and preserves a server collection conflict', async () => {
    const user = userEvent.setup();
    mocks.phase5Mutation.mockRejectedValueOnce(new Error('Mixed-funded recovery requires full collection.'));
    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: 'Open' }));
    await user.click(screen.getByRole('button', { name: 'Confirm capital recovery' }));
    await user.type(screen.getByLabelText(/Recovery confirmation reason/), 'Reviewed collected capital');
    await user.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(mocks.phase5Mutation).toHaveBeenCalledWith(
      ids.company, ids.user, 'investment', 'sales/66666666-6666-4666-8666-666666666666/capital-recoveries/',
      { expected_source_version: 'a'.repeat(64), reason: 'Reviewed collected capital' }, 'POST',
    ));
    expect(await screen.findByText('Mixed-funded recovery requires full collection.')).toBeInTheDocument();
    expect(screen.getByLabelText(/Recovery confirmation reason/)).toHaveValue('Reviewed collected capital');
  });

  it('records a partial payment for a current confirmed Investor result and refreshes from the server', async () => {
    const user = userEvent.setup();
    const bank = { id: ids.account, account_type: 'BANK' as const, label: 'Main Bank', is_active: true };
    mocks.phase5Api.vehicles.mockResolvedValue({
      ...baseVehicles,
      results: [{ ...baseVehicles.results[0], is_sold: true, sale_id: ids.sale }],
    });
    mocks.phase5Api.sale.mockResolvedValue({
      id: ids.sale, branch_id: ids.branch, buyer_name: 'Maya', buyer_phone: '9876543210',
      sale_price: '12000.00', received_total: '12000.00', refunded_total: '0.00',
      net_received: '12000.00', receivable: '0.00', refund_payable: '0.00',
      investor_funded: true, corrections: [], receipts: [], refunds: [],
    });
    mocks.phase5Api.vehicleFinancialPosition.mockResolvedValue({
      vehicle_id: ids.vehicle, company_id: ids.company, branch_id: ids.branch,
      purchase_id: '55555555-5555-4555-8555-555555555556', sale_id: ids.sale,
      investor_id: ids.investor, investor_share_agreement_id: null,
      investor_share_percentage_snapshot: '35.0000', profit_share_status: 'AVAILABLE',
      purchase_cost: '10000.00', vehicle_expense_cost: '0.00', total_vehicle_cost: '10000.00',
      investor_fund_cost: '6000.00', running_capital_cost: '4000.00', sale_price: '12000.00',
      actual_net_collection: '12000.00', buyer_receivable: '0.00', buyer_refund_payable: '0.00',
      calculated_result: '2000.00', status: 'READY_FOR_REVIEW', settlement_eligible: false,
      capital_recovery: { investor_principal: '6000.00', running_capital: '4000.00', is_current: true, is_complete: true },
      source_version: 'a'.repeat(64), purchase_correction_version: 0,
      expense_correction_versions: [], sale_correction_version: 0,
      confirmed_result: {
        id: ids.result, version: 1, source_version: 'a'.repeat(64), is_current: true,
        result_kind: 'PROFIT', result_amount: '2000.00', investor_share_amount: '700.00',
        investor_profit_paid: '0.00', investor_profit_remaining: '700.00', investor_profit_overpaid: '0.00',
        company_share_amount: '1300.00', confirmed_at: '2026-11-19T00:00:00Z', reason: 'Verified result',
      },
    });
    mocks.phase5Api.paymentAccountPreference.mockResolvedValue({ company_id: ids.company, account_id: null, account_label: null });
    mocks.accountingAccounts.mockResolvedValue([bank]);
    mocks.phase5Api.recordInvestorVehicleProfitPayment.mockResolvedValue({ payment_id: ids.result });

    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: 'Open' }));
    await user.click(await screen.findByRole('button', { name: 'Record Investor Profit payment' }));
    await user.selectOptions(await screen.findByLabelText(/Cash \/ Bank account/), ids.account);
    await user.type(screen.getByLabelText(/Investor Profit payment/), '250.00');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(mocks.phase5Api.recordInvestorVehicleProfitPayment).toHaveBeenCalledWith(
      ids.company,
      ids.user,
      ids.result,
      expect.objectContaining({ account_id: ids.account, amount: '250.00' }),
    ));
    expect(await screen.findByRole('status')).toHaveTextContent('Saved successfully');
  });

  it('lets an authorized Accountant offset a confirmed Loss against a later available Vehicle Profit', async () => {
    const user = userEvent.setup();
    const profitResultId = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
    mocks.phase5Api.vehicles.mockResolvedValue({
      ...baseVehicles,
      results: [{ ...baseVehicles.results[0], is_sold: true, sale_id: ids.sale }],
    });
    mocks.phase5Api.sale.mockResolvedValue({
      id: ids.sale, branch_id: ids.branch, buyer_name: 'Maya', buyer_phone: '9876543210',
      sale_price: '8000.00', received_total: '8000.00', refunded_total: '0.00',
      net_received: '8000.00', receivable: '0.00', refund_payable: '0.00',
      investor_funded: true, corrections: [], receipts: [], refunds: [],
    });
    mocks.phase5Api.vehicleFinancialPosition.mockResolvedValue({
      vehicle_id: ids.vehicle, company_id: ids.company, branch_id: ids.branch,
      purchase_id: '55555555-5555-4555-8555-555555555556', sale_id: ids.sale,
      investor_id: ids.investor, investor_share_agreement_id: null,
      investor_share_percentage_snapshot: '40.0000', profit_share_status: 'AVAILABLE',
      purchase_cost: '10000.00', vehicle_expense_cost: '0.00', total_vehicle_cost: '10000.00',
      investor_fund_cost: '6000.00', running_capital_cost: '4000.00', sale_price: '8000.00',
      actual_net_collection: '8000.00', buyer_receivable: '0.00', buyer_refund_payable: '0.00',
      calculated_result: '-2000.00', status: 'LOSS_REVIEW_REQUIRED', settlement_eligible: false,
      source_version: 'a'.repeat(64), purchase_correction_version: 0,
      expense_correction_versions: [], sale_correction_version: 0,
      confirmed_result: {
        id: ids.result, version: 1, source_version: 'a'.repeat(64), is_current: true,
        result_kind: 'LOSS', result_amount: '-2000.00', investor_share_amount: '-800.00',
        investor_profit_paid: '0.00', investor_profit_remaining: '0.00', investor_profit_overpaid: '0.00',
        company_share_amount: '-1200.00', suggested_investor_loss: '700.00', suggested_company_loss: '1300.00', confirmed_at: '2026-11-19T00:00:00Z', reason: 'Reviewed Loss',
      },
    });
    mocks.phase5Api.investorProfitLossOffsetOptions.mockResolvedValue({
      loss_result_id: ids.result,
      loss_remaining_amount: '800.00',
      target_options: [{
        result_id: profitResultId, vehicle_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
        registration: 'KL 11 P 6060', model: 'Sedan', sale_branch_id: ids.branch,
        sale_date: '2026-11-18', investor_share_amount: '1000.00', remaining_amount: '1000.00',
      }],
    });
    mocks.phase5Api.recordInvestorProfitLossOffset.mockResolvedValue({ offset_id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd' });

    renderView('Stock / Investor');
    await user.click(await screen.findByRole('button', { name: 'Open' }));
    expect(await screen.findByText(/Original suggestion:/)).toHaveTextContent('700.00');
    await user.click(await screen.findByRole('button', { name: 'Apply Loss to available Profit' }));
    await user.type(await screen.findByLabelText('Offset amount'), '300.00');
    await user.type(screen.getByLabelText('Reason'), 'Apply reviewed loss');
    await user.click(screen.getByRole('button', { name: 'Save Loss offset' }));

    await waitFor(() => expect(mocks.phase5Api.recordInvestorProfitLossOffset).toHaveBeenCalledWith(
      ids.company, ids.user, ids.result,
      { profit_result_id: profitResultId, amount: '300.00', reason: 'Apply reviewed loss' },
    ));
    expect(await screen.findByText('Loss offset recorded. No Cash/Bank movement was created.')).toBeInTheDocument();
  });

  it('shows audited Sale price corrections in the Sales history after loading backend data', async () => {
    const user = userEvent.setup();
    mocks.phase5Api.sales.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: '55555555-5555-4555-8555-555555555555',
        company_id: ids.company,
        vehicle_id: ids.vehicle,
        vehicle_registration: 'KL 11 P 5050',
        vehicle_model: 'Hatchback',
        branch_id: ids.branch,
        branch_name: 'Central',
        sale_price: '11000.00',
        investor_funded: false,
        buyer_name: 'Maya',
        buyer_phone: '9876543210',
        sold_at: '2026-11-11T08:00:00Z',
        received_total: '2000.00',
        refunded_total: '0.00',
        net_received: '2000.00',
        receivable: '9000.00',
        refund_payable: '0.00',
        refund_available: '0.00',
        correction_version: 1,
        receipts: [],
        refunds: [],
        corrections: [{
          id: '66666666-6666-4666-8666-666666666666',
          version: 1,
          previous_sale_price: '12000.00',
          sale_price: '11000.00',
          reason: 'Signed amount corrected.',
          effective_at: '2026-11-11T08:00:00Z',
          recorded_at: '2026-11-12T08:00:00Z',
        }],
      }],
    });

    renderView('Sale Corrections & Refunds');

    await user.click(await screen.findByText('Price correction history (1)'));
    expect(screen.getByText('Signed amount corrected.')).toBeInTheDocument();
    expect(screen.getByText(/12,000.*11,000/)).toBeInTheDocument();
    expect(screen.getByText(/Recorded/)).toBeInTheDocument();
  });

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

  it('saves an Investor Profit calendar only after the backend accepts it', async () => {
    const user = userEvent.setup();
    const investorId = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
    mocks.phase5Api.investors.mockResolvedValue({
      count: 1, next: null, previous: null,
      results: [{ id: investorId, company_id: ids.company, name: 'Investor', is_active: true }],
    });
    renderView('Investor Fund');
    await screen.findByRole('option', { name: 'Investor' });
    await user.selectOptions(await screen.findByLabelText('Filter by Investor'), investorId);
    expect(await screen.findByRole('region', { name: 'Investor Profit calendar settings' })).toBeInTheDocument();
    await user.type(screen.getByLabelText('Period start date'), '2026-11-19');
    await user.clear(screen.getByLabelText('Duration (months)'));
    await user.type(screen.getByLabelText('Duration (months)'), '6');
    await user.click(screen.getByRole('button', { name: 'Save calendar' }));

    await waitFor(() => expect(mocks.phase5Api.configureProfitCalendar).toHaveBeenCalledWith(
      ids.company, ids.user, investorId,
      { effective_start: '2026-11-19', duration_months: 6 },
    ));
    expect(await screen.findByRole('status')).toHaveTextContent('Calendar version 1 saved.');
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
