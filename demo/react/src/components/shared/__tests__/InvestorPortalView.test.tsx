import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InvestorPortalView } from '../InvestorPortalView';

const ids = {
  user: '11111111-1111-4111-8111-111111111111',
  company: '22222222-2222-4222-8222-222222222222',
  investor: '33333333-3333-4333-8333-333333333333',
  binding: '44444444-4444-4444-8444-444444444444',
  vehicle: '55555555-5555-4555-8555-555555555555',
  exit: '66666666-6666-4666-8666-666666666666',
};

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  investorPortalSelf: vi.fn(),
  investorPortalFundHistory: vi.fn(),
  investorPortalInterimPaymentHistory: vi.fn(),
  requestInvestorExit: vi.fn(),
  requestInvestorExitCancellation: vi.fn(),
}));

vi.mock('../../../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../../../api/phase5Api', () => ({
  phase5Api: {
    investorPortalSelf: mocks.investorPortalSelf,
    investorPortalFundHistory: mocks.investorPortalFundHistory,
    investorPortalInterimPaymentHistory: mocks.investorPortalInterimPaymentHistory,
    requestInvestorExit: mocks.requestInvestorExit,
    requestInvestorExitCancellation: mocks.requestInvestorExitCancellation,
  },
}));

const snapshot = () => ({
  investor_id: ids.investor,
  name: 'Private Investor',
  binding_id: ids.binding,
  fund_position: {
    credit_total: '50000.00', principal_return_total: '0.00', committed_vehicle_total: '30000.00',
    use_adjustment_total: '0.00', ledger_available_amount: '20000.00', withdrawal_eligible: false,
    status: 'PHASE8_RECONCILIATION_REQUIRED',
  },
  vehicles: [{
    vehicle_id: ids.vehicle, registration: 'KL 11 P 5050', model: 'Hatchback', branch_name: 'Central',
    sale_status: 'NOT_SOLD', confirmed_result_status: 'NOT_CONFIRMED',
  }],
  interim: { status: 'CONFIGURED', monthly_amount: '1000.00', effective_date: '2026-01-01', payout_status: 'NOT_RECONCILED' },
  profit_calendar: { status: 'DEFAULT_FROM_FIRST_FUND_CREDIT', start_date: '2026-01-15', duration_months: 6, source: 'DEFAULT_SIX_MONTHS' },
  profit_period_status: 'CALCULATED_NOT_RECONCILED',
  unassigned_result_count: 0,
    profit_periods: [{ period_start: '2026-01-15', period_end: '2026-07-14', duration_months: 6, gross_investor_profit: '1000.00', investor_loss_share: '250.00', deal_profit_paid: '300.00', interim_paid: '200.00', loss_offset_applied: '100.00', result_count: 2, status: 'CALCULATED_NOT_RECONCILED', paid_status: 'NOT_RECONCILED', reconciliation_status: 'NOT_RECONCILED', confirmed_snapshot: null }],
  vehicle_results: [],
  exit_requests: [],
});

function renderView(routeKey = 'Investor Fund') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  render(<QueryClientProvider client={queryClient}><InvestorPortalView routeKey={routeKey} /></QueryClientProvider>);
  return queryClient;
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.useAuth.mockReturnValue({
    status: 'authenticated', user: { id: ids.user }, currentCompany: { id: ids.company },
  });
  mocks.investorPortalSelf.mockImplementation(async () => snapshot());
  mocks.investorPortalFundHistory.mockResolvedValue({
    count: 0, next: null, previous: null, results: [],
  });
  mocks.investorPortalInterimPaymentHistory.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.requestInvestorExit.mockResolvedValue({ id: ids.exit, status: 'REQUESTED' });
  mocks.requestInvestorExitCancellation.mockResolvedValue({ id: ids.exit, status: 'CANCELLATION_PENDING' });
});

describe('Investor portal', () => {
  it('shows only the bound profile and never labels the ledger balance withdrawable', async () => {
    renderView('Investor Fund');
    expect(await screen.findByText(/Private Investor/)).toBeInTheDocument();
    expect(screen.getByText(/not a confirmed withdrawal amount/i)).toBeInTheDocument();
    expect(screen.getByText('₹20,000.00')).toBeInTheDocument();
    expect(screen.queryByText(/Company share/i)).not.toBeInTheDocument();
    expect(mocks.investorPortalSelf).toHaveBeenCalledWith(ids.company, expect.any(AbortSignal));
  });

  it('shows paginated own Fund activity without displaying payment references', async () => {
    mocks.investorPortalFundHistory.mockResolvedValue({
      count: 2, next: null, previous: null,
      results: [
        { id: ids.exit, effective_at: '2026-05-03T09:00:00Z', amount: '30000.00', activity_type: 'FUND_CREDIT', branch_name: 'Central', vehicle_registration: null },
        { id: ids.vehicle, effective_at: '2026-05-04T09:00:00Z', amount: '-30000.00', activity_type: 'VEHICLE_COMMITMENT', branch_name: 'Central', vehicle_registration: 'KL 11 P 5050' },
      ],
    });
    renderView('Investor Fund');
    expect(await screen.findByText('Fund activity history')).toBeInTheDocument();
    expect(await screen.findByText('Fund credited')).toBeInTheDocument();
    expect(await screen.findByText(/Committed to Vehicle · KL 11 P 5050/)).toBeInTheDocument();
    expect(await screen.findByText('-₹30,000.00')).toBeInTheDocument();
    expect(mocks.investorPortalFundHistory).toHaveBeenCalledWith(ids.company, 1, expect.any(AbortSignal));
  });

  it('hides unreconciled fund totals when a corrected credit needs manual review', async () => {
    mocks.investorPortalSelf.mockResolvedValue({
      ...snapshot(),
      fund_position: {
        credit_total: null, principal_return_total: null, committed_vehicle_total: null,
        use_adjustment_total: null, ledger_available_amount: null, withdrawal_eligible: false,
        status: 'MANUAL_REVIEW_REQUIRED',
      },
    });
    renderView('Investor Fund');
    expect(await screen.findByText(/Manual review required/i)).toBeInTheDocument();
    expect(screen.queryByText('₹50,000.00')).not.toBeInTheDocument();
    expect(screen.queryByText('₹20,000.00')).not.toBeInTheDocument();
  });

  it('shows Sale-date period gross totals without turning them into a payable', async () => {
    renderView('Investor Profit & Interim');
    expect(await screen.findByText(/Profit periods · calculated not reconciled/i)).toBeInTheDocument();
    expect(screen.getByText(/Gross profit ₹1,000.00 · Deal paid ₹300.00 · Interim paid ₹200.00 · Loss ₹250.00 · Offset ₹100.00/i)).toBeInTheDocument();
    expect(screen.getByText(/does not establish a payable balance/i)).toBeInTheDocument();
    expect(mocks.investorPortalInterimPaymentHistory).toHaveBeenCalledWith(ids.company, 1, expect.any(AbortSignal));
  });

  it('shows recorded Deal Profit payments for its own Vehicles without exposing a period payable', async () => {
    mocks.investorPortalSelf.mockResolvedValue({
      ...snapshot(),
      vehicles: [{
        ...snapshot().vehicles[0], confirmed_result_status: 'CURRENT',
        confirmed_result: { result_kind: 'PROFIT', investor_share_amount: '1000.00', deal_profit_paid: '300.00', loss_offset_applied: '100.00', confirmed_at: '2026-06-01T10:00:00Z', current: true },
      }],
      vehicle_results: [{ vehicle_id: ids.vehicle, sale_id: ids.exit, effective_sale_date: '2026-06-01', status: 'CURRENT', result_kind: 'PROFIT', investor_share_amount: '1000.00', deal_profit_paid: '300.00', loss_offset_applied: '100.00', confirmed_at: '2026-06-01T10:00:00Z', current: true }],
    });
    renderView('Investor Profit & Interim');
    expect(await screen.findByText(/Investor share ₹1,000.00 · offset ₹100.00 · paid ₹300.00/)).toBeInTheDocument();
    expect(screen.getByText(/Deal paid ₹300.00/)).toBeInTheDocument();
    expect(screen.queryByText(/remaining payable|balance due/i)).not.toBeInTheDocument();
  });

  it('shows paginated actual Interim payments as history, not as a final payable', async () => {
    mocks.investorPortalInterimPaymentHistory.mockResolvedValue({
      count: 1, next: null, previous: null,
      results: [{ id: ids.exit, period_month: '2026-05-01', effective_at: '2026-05-20T09:00:00Z', amount: '400.00' }],
    });
    renderView('Investor Profit & Interim');
    expect(await screen.findByText('Interim payment history')).toBeInTheDocument();
    expect(await screen.findByText(/Interim payment · 1 May 2026/i)).toBeInTheDocument();
    expect(screen.getByText('₹400.00')).toBeInTheDocument();
    expect(screen.queryByText(/remaining payable|balance due/i)).not.toBeInTheDocument();
  });

  it('does not display internal vehicle costs, protected agreement values, or buyer balances', async () => {
    const privateFields = {
      ...snapshot(),
      vehicles: [{
        ...snapshot().vehicles[0], purchase_cost: '30000.00', vehicle_expense_cost: '1000.00',
        total_vehicle_cost: '31000.00', investor_share_percentage_snapshot: '33.0000',
        sale_price: '40000.00', actual_net_collection: '20000.00', buyer_receivable: '20000.00',
      }],
    };
    mocks.investorPortalSelf.mockResolvedValue(privateFields);
    renderView('Stock / Investor');
    expect(await screen.findByText('KL 11 P 5050 · Hatchback')).toBeInTheDocument();
    expect(screen.getByText(/Sale\/collection status: not sold/i)).toBeInTheDocument();
    expect(screen.queryByText('₹30,000.00')).not.toBeInTheDocument();
    expect(screen.queryByText('₹31,000.00')).not.toBeInTheDocument();
    expect(screen.queryByText('33.0000%')).not.toBeInTheDocument();
    expect(screen.queryByText(/Buyer due/i)).not.toBeInTheDocument();
  });

  it('formats large Investor balances without JavaScript floating-point rounding', async () => {
    mocks.investorPortalSelf.mockImplementation(async () => ({
      ...snapshot(),
      fund_position: { ...snapshot().fund_position, credit_total: '9007199254740993.01' },
    }));
    renderView('Investor Fund');
    expect(await screen.findByText('₹9,00,71,99,25,47,40,993.01')).toBeInTheDocument();
  });

  it('requires terms acceptance and refreshes the canonical profile after Exit request', async () => {
    const user = userEvent.setup();
    let requested = false;
    mocks.investorPortalSelf.mockImplementation(async () => ({
      ...snapshot(),
      exit_requests: requested ? [{
        id: ids.exit, status: 'REQUESTED', terms_version: 'investor-exit-request-v1',
        terms_accepted_at: '2026-11-19T00:00:00Z', requested_at: '2026-11-19T00:00:00Z', history: [],
        initial_notice_deadline: '2027-02-19T00:00:00Z', notice_deadline: '2027-04-19T00:00:00Z',
        notice_extensions: [{ id: ids.exit, version: 1, previous_deadline: '2027-02-19T00:00:00Z', deadline: '2027-04-19T00:00:00Z', reason: 'Reviewed', recorded_at: '2026-11-20T00:00:00Z' }],
      }] : [],
    }));
    mocks.requestInvestorExit.mockImplementation(async () => { requested = true; return { id: ids.exit, status: 'REQUESTED' }; });
    renderView('Reconciliation & Settlement');
    expect(await screen.findByText(/normal Exit notice is three months/i)).toBeInTheDocument();
    expect(screen.getByText(/new Fund credits and new Vehicle purchases using this Fund are blocked/i)).toBeInTheDocument();
    const submit = await screen.findByRole('button', { name: /submit exit request/i });
    expect(submit).toBeDisabled();
    await user.click(screen.getByRole('checkbox'));
    await user.click(submit);
    await waitFor(() => expect(mocks.requestInvestorExit).toHaveBeenCalledWith(ids.company, ids.user));
    expect(await screen.findByText(/REQUESTED/)).toBeInTheDocument();
    expect(screen.getByText(/extended by Company Accountant/)).toBeInTheDocument();
    expect(mocks.investorPortalSelf.mock.calls.length).toBeGreaterThan(1);
  });

  it('shows the last confirmed calculation with a restatement warning without calling it payable', async () => {
    mocks.investorPortalSelf.mockResolvedValue({
      ...snapshot(),
      profit_period_status: 'RESTATEMENT_REQUIRED',
      profit_periods: [{
        ...snapshot().profit_periods[0],
        reconciliation_status: 'RESTATEMENT_REQUIRED',
        confirmed_snapshot: {
          version: 2, confirmed_at: '2026-07-15T10:00:00Z',
          gross_investor_profit: '1000.00', investor_loss_share: '250.00',
          deal_profit_paid: '350.00', interim_paid: '200.00', loss_offset_applied: '100.00',
          net_position: '350.00', restatement_adjustment: '-50.00',
          pending_restatement_adjustment: '-50.00',
          notice: 'Confirmed calculation snapshot only; not a payable, payment, or final settlement.',
        },
      }],
    });
    renderView('Investor Profit & Interim');
    expect(await screen.findByText(/Last Accountant-confirmed calculation: ₹350.00 · version 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Source records changed\. Difference awaiting review: -₹50\.00\. This is not a payment or deduction\./i)).toBeInTheDocument();
    expect(screen.getByText(/This signed calculation is not a payable or settlement\./i)).toBeInTheDocument();
  });

  it('keeps a failed Exit request visible without a success state', async () => {
    const user = userEvent.setup();
    mocks.requestInvestorExit.mockRejectedValue(new Error('Server rejected request'));
    renderView('Reconciliation & Settlement');
    await screen.findByRole('button', { name: /submit exit request/i });
    await user.click(screen.getByRole('checkbox'));
    await user.click(screen.getByRole('button', { name: /submit exit request/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Server rejected request');
    expect(screen.queryByText(/submitted successfully/i)).not.toBeInTheDocument();
  });
});
