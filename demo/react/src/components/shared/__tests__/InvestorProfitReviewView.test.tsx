import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InvestorProfitReviewView } from '../InvestorProfitReviewView';

const ids = {
  user: '11111111-1111-4111-8111-111111111111',
  company: '22222222-2222-4222-8222-222222222222',
  investor: '33333333-3333-4333-8333-333333333333',
};

const mocks = vi.hoisted(() => ({
  reconciliationSaved: false,
  positionSaved: false,
  useAuth: vi.fn(),
  investors: vi.fn(),
  investorProfitPeriodProjection: vi.fn(),
  reconcileInvestorProfitPeriod: vi.fn(),
  confirmInvestorProfitPosition: vi.fn(),
  investorPortalBinding: vi.fn(),
  bindInvestorPortalAccount: vi.fn(),
  revokeInvestorPortalBinding: vi.fn(),
  investorExitRequests: vi.fn(),
  investorExitSettlementPosition: vi.fn(),
  extendInvestorExitNotice: vi.fn(),
  reviewInvestorExitCancellation: vi.fn(),
}));

vi.mock('../../../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../../../api/phase5Api', () => ({
  phase5Api: {
    investors: mocks.investors,
    investorProfitPeriodProjection: mocks.investorProfitPeriodProjection,
    reconcileInvestorProfitPeriod: mocks.reconcileInvestorProfitPeriod,
    confirmInvestorProfitPosition: mocks.confirmInvestorProfitPosition,
    investorPortalBinding: mocks.investorPortalBinding,
    bindInvestorPortalAccount: mocks.bindInvestorPortalAccount,
    revokeInvestorPortalBinding: mocks.revokeInvestorPortalBinding,
    investorExitRequests: mocks.investorExitRequests,
    investorExitSettlementPosition: mocks.investorExitSettlementPosition,
    extendInvestorExitNotice: mocks.extendInvestorExitNotice,
    reviewInvestorExitCancellation: mocks.reviewInvestorExitCancellation,
  },
}));

const projection = () => ({
  company_id: ids.company,
  investor_id: ids.investor,
  calendar: { status: 'CONFIGURED', start_date: '2026-01-15', duration_months: 6, versions: [] },
  status: 'CALCULATED_NOT_RECONCILED',
  periods: [{
    period_start: '2026-01-15', period_end: '2026-07-14', duration_months: 6,
    gross_investor_profit: '100000.00', investor_loss_share: '5000.00',
    deal_profit_paid: '25000.00', loss_offset_applied: '1000.00',
    interim_paid: '5000.00',
    result_count: 2, status: 'CALCULATED_NOT_RECONCILED', paid_status: 'NOT_RECONCILED',
    source_version: 'a'.repeat(64),
    reconciliation_status: mocks.reconciliationSaved ? 'RECONCILED' : 'NOT_RECONCILED',
    reconciliation_id: mocks.reconciliationSaved ? '66666666-6666-4666-8666-666666666666' : null,
    reconciliation_version: mocks.reconciliationSaved ? 1 : null,
    last_reconciled_net_position: mocks.reconciliationSaved ? '69000.00' : null,
    last_restatement_adjustment: mocks.reconciliationSaved ? '0.00' : null,
    pending_restatement_adjustment: null,
    confirmed_position: mocks.positionSaved ? {
      id: '77777777-7777-4777-8777-777777777777', kind: 'PAYABLE', amount: '69000.00',
      is_current: true, source_version: 'a'.repeat(64), reason: 'Confirm remaining position',
      confirmed_at: '2026-11-19T10:00:00Z',
    } : null,
  }],
  unassigned_result_count: 0,
  settlement_status: 'NOT_IMPLEMENTED',
  notice: 'Calculation only.',
});

function renderView() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(<QueryClientProvider client={queryClient}><InvestorProfitReviewView /></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.reconciliationSaved = false;
  mocks.positionSaved = false;
  mocks.useAuth.mockReturnValue({
    user: { id: ids.user },
    currentCompany: { id: ids.company, company_wide_roles: ['accountant'] },
  });
  mocks.investors.mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: ids.investor, company_id: ids.company, name: 'Nila', is_active: true }] });
  mocks.investorProfitPeriodProjection.mockImplementation(async () => projection());
  mocks.reconcileInvestorProfitPeriod.mockImplementation(async () => {
    mocks.reconciliationSaved = true;
    return {
      id: '66666666-6666-4666-8666-666666666666',
      investor_id: ids.investor,
      period_start: '2026-01-15',
      period_end: '2026-07-14',
      duration_months: 6,
      result_count: 2,
      version: 1,
      source_version: 'a'.repeat(64),
      gross_investor_profit: '100000.00',
      investor_loss_share: '5000.00',
      deal_profit_paid: '25000.00',
      interim_paid: '5000.00',
      loss_offset_applied: '1000.00',
      net_position: '69000.00',
      restatement_adjustment: '0.00',
      previous_reconciliation_id: null,
      reason: 'Reviewed source totals',
      confirmed_at: '2026-11-19T10:00:00Z',
      confirmed_by_id: ids.user,
    };
  });
  mocks.investorPortalBinding.mockResolvedValue(null);
  mocks.investorExitRequests.mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  mocks.investorExitSettlementPosition.mockResolvedValue({
    investor_id: ids.investor, exit_request_id: '55555555-5555-4555-8555-555555555555',
    notice_deadline: '2027-02-19T00:00:00Z', principal_available: '9000.00',
    residual_confirmed_loss: '250.00', vehicles: [], confirmed_positions: [], confirmed_losses: [],
    blockers: ['BUYER_PRINCIPAL_REFUND_OPEN'], settlement_order: ['PRINCIPAL', 'RESIDUAL_LOSS', 'REMAINING_PROFIT', 'CLOSE'],
    closure_implemented: false, source_version: 'a'.repeat(64),
  });
  mocks.extendInvestorExitNotice.mockResolvedValue({});
  mocks.reviewInvestorExitCancellation.mockResolvedValue({});
  mocks.bindInvestorPortalAccount.mockResolvedValue({
    id: '55555555-5555-4555-8555-555555555555', investor_id: ids.investor,
    account_id: ids.user, login_id: 'investor.login', effective_from: '2026-11-19T00:00:00Z', effective_until: null,
  });
  mocks.revokeInvestorPortalBinding.mockResolvedValue({
    id: '55555555-5555-4555-8555-555555555555', investor_id: ids.investor,
    account_id: ids.user, login_id: 'investor.login', effective_from: '2026-11-19T00:00:00Z', effective_until: '2026-11-20T00:00:00Z',
  });
});

describe('InvestorProfitReviewView', () => {
  it('shows current Exit blockers without implying that a payment was made', async () => {
    mocks.investorExitRequests.mockResolvedValue({ count: 1, next: null, previous: null, results: [{
      id: '55555555-5555-4555-8555-555555555555', status: 'REQUESTED',
      requested_at: '2026-11-19T00:00:00Z', notice_deadline: '2027-02-19T00:00:00Z',
      cancellation_reason: null,
    }] });
    renderView();
    expect(await screen.findByText('Available principal:')).toBeInTheDocument();
    expect(await screen.findByText('BUYER PRINCIPAL REFUND OPEN')).toBeInTheDocument();
    expect(screen.getByText(/does not close Exit/)).toBeInTheDocument();
  });
  it.each([
    ['principal remains', '9000.00', '0.00'],
    ['confirmed Loss remains', '0.00', '250.00'],
    ['principal needs review', null, '0.00'],
  ])('keeps Exit Profit payment unavailable while %s', async (_label, principal, loss) => {
    mocks.investorExitRequests.mockResolvedValue({ count: 1, next: null, previous: null, results: [{
      id: '55555555-5555-4555-8555-555555555555', status: 'REQUESTED',
      requested_at: '2026-11-19T00:00:00Z', notice_deadline: '2027-02-19T00:00:00Z',
      cancellation_reason: null,
    }] });
    mocks.investorExitSettlementPosition.mockResolvedValue({
      investor_id: ids.investor, exit_request_id: '55555555-5555-4555-8555-555555555555',
      notice_deadline: '2027-02-19T00:00:00Z', principal_available: principal,
      residual_confirmed_loss: loss, vehicles: [], confirmed_positions: [{
        id: '88888888-8888-4888-8888-888888888888', kind: 'PAYABLE', amount: '100.00',
        is_current: true, source_version: 'a'.repeat(64),
      }], confirmed_losses: [], blockers: ['EXIT_NOTICE_NOT_EXPIRED'],
      settlement_order: ['PRINCIPAL', 'RESIDUAL_LOSS', 'REMAINING_PROFIT', 'CLOSE'],
      closure_implemented: false, source_version: 'a'.repeat(64),
    });
    renderView();
    expect(await screen.findByText('Settle Principal and confirmed Loss first.')).toBeInTheDocument();
    expect(screen.queryByRole('form', { name: 'Exit Profit payment' })).not.toBeInTheDocument();
  });
  it('shows the Exit Profit payment form after server-confirmed Principal and Loss settlement', async () => {
    mocks.investorExitRequests.mockResolvedValue({ count: 1, next: null, previous: null, results: [{
      id: '55555555-5555-4555-8555-555555555555', status: 'REQUESTED',
      requested_at: '2026-11-19T00:00:00Z', notice_deadline: '2027-02-19T00:00:00Z',
      cancellation_reason: null,
    }] });
    mocks.investorExitSettlementPosition.mockResolvedValue({
      investor_id: ids.investor, exit_request_id: '55555555-5555-4555-8555-555555555555',
      notice_deadline: '2027-02-19T00:00:00Z', principal_available: '0.00',
      residual_confirmed_loss: '0.00', vehicles: [], confirmed_positions: [{
        id: '88888888-8888-4888-8888-888888888888', kind: 'PAYABLE', amount: '100.00',
        is_current: true, source_version: 'a'.repeat(64),
      }], confirmed_losses: [], blockers: [],
      settlement_order: ['PRINCIPAL', 'RESIDUAL_LOSS', 'REMAINING_PROFIT', 'CLOSE'],
      closure_implemented: false, source_version: 'a'.repeat(64),
    });
    renderView();
    expect(await screen.findByRole('form', { name: 'Exit Profit payment' })).toBeInTheDocument();
  });
  it('confirms a payable only through the position action and reloads server truth', async () => {
    const user = userEvent.setup();
    mocks.reconciliationSaved = true;
    mocks.confirmInvestorProfitPosition.mockImplementation(async () => {
      mocks.positionSaved = true;
      return projection().periods[0].confirmed_position;
    });
    renderView();
    await user.type(await screen.findByLabelText(/Position confirmation reason for/), 'Confirm remaining position');
    await user.click(screen.getByRole('button', { name: 'Confirm payable / recoverable' }));
    await waitFor(() => expect(mocks.confirmInvestorProfitPosition).toHaveBeenCalledWith(
      ids.company, ids.user, ids.investor, {
        reconciliation_id: '66666666-6666-4666-8666-666666666666',
        expected_source_version: 'a'.repeat(64), reason: 'Confirm remaining position',
      },
    ));
    expect(await screen.findByText(/Confirmed payable:/)).toHaveTextContent('69,000');
    expect(mocks.reconcileInvestorProfitPeriod).not.toHaveBeenCalled();
  });
  it('reviews a pending Investor cancellation without claiming success before the server accepts', async () => {
    const user = userEvent.setup();
    mocks.investorExitRequests.mockResolvedValue({ count: 1, next: null, previous: null, results: [{
      id: '55555555-5555-4555-8555-555555555555', status: 'CANCELLATION_PENDING',
      requested_at: '2026-11-19T00:00:00Z', notice_deadline: '2027-02-19T00:00:00Z',
      cancellation_reason: 'Plans changed',
    }] });
    mocks.reviewInvestorExitCancellation.mockRejectedValueOnce(new Error('Review was rejected'));
    renderView();
    expect(await screen.findByText(/Plans changed/)).toBeInTheDocument();
    await user.type(screen.getByLabelText('Review note (optional)'), 'Checked with Investor');
    await user.click(screen.getByRole('button', { name: 'Approve cancellation' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Review was rejected');
    expect(screen.getByLabelText('Review note (optional)')).toHaveValue('Checked with Investor');
    expect(mocks.reviewInvestorExitCancellation).toHaveBeenCalledWith(
      ids.company, ids.user, ids.investor, '55555555-5555-4555-8555-555555555555',
      true, 'Checked with Investor',
    );
    await user.click(screen.getByRole('button', { name: 'Keep Exit open' }));
    await waitFor(() => expect(mocks.reviewInvestorExitCancellation).toHaveBeenCalledWith(
      ids.company, ids.user, ids.investor, '55555555-5555-4555-8555-555555555555',
      false, 'Checked with Investor',
    ));
  });
  it('extends an open Exit only after an Accountant supplies a deadline and reason', async () => {
    const user = userEvent.setup();
    mocks.investorExitRequests.mockResolvedValue({ count: 1, next: null, previous: null, results: [{
      id: '55555555-5555-4555-8555-555555555555', status: 'REQUESTED',
      requested_at: '2026-11-19T00:00:00Z', notice_deadline: '2027-02-19T00:00:00Z',
    }] });
    renderView();
    await screen.findByText(/Current deadline:/);
    await user.type(screen.getByLabelText('New deadline'), '2027-04-20T10:30');
    await user.type(screen.getByLabelText('Reason'), 'Vehicle remains open');
    await user.click(screen.getByRole('button', { name: 'Extend notice' }));
    await waitFor(() => expect(mocks.extendInvestorExitNotice).toHaveBeenCalledWith(
      ids.company, ids.user, ids.investor, '55555555-5555-4555-8555-555555555555',
      expect.any(String), 'Vehicle remains open',
    ));
  });

  it('keeps extension details visible when the server rejects an Exit extension', async () => {
    const user = userEvent.setup();
    mocks.investorExitRequests.mockResolvedValue({ count: 1, next: null, previous: null, results: [{
      id: '55555555-5555-4555-8555-555555555555', status: 'REQUESTED',
      requested_at: '2026-11-19T00:00:00Z', notice_deadline: '2027-02-19T00:00:00Z',
    }] });
    mocks.extendInvestorExitNotice.mockRejectedValue(new Error('Deadline is not later'));
    renderView();
    await screen.findByText(/Current deadline:/);
    await user.type(screen.getByLabelText('New deadline'), '2027-04-20T10:30');
    await user.type(screen.getByLabelText('Reason'), 'Vehicle remains open');
    await user.click(screen.getByRole('button', { name: 'Extend notice' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Deadline is not later');
    expect(screen.getByLabelText('Reason')).toHaveValue('Vehicle remains open');
  });
  it('shows gross calculation while withholding absent paid and payable ledgers', async () => {
    renderView();
    expect(await screen.findByRole('heading', { name: 'Investor Profit period review' })).toBeInTheDocument();
    expect(await screen.findByText('Nila')).toBeInTheDocument();
    expect(await screen.findByText('₹1,00,000.00')).toBeInTheDocument();
    expect(screen.getAllByText('₹5,000.00')).toHaveLength(2);
    expect(screen.getByText(/Confirming a period stores an audited calculation snapshot/i)).toBeInTheDocument();
    expect(screen.getByText('₹1,000.00')).toBeInTheDocument();
    expect(screen.getByText('NOT RECONCILED')).toBeInTheDocument();
    expect(screen.queryByText(/Payable:/i)).not.toBeInTheDocument();
    expect(screen.getByText('₹25,000.00')).toBeInTheDocument();
    expect(mocks.investorProfitPeriodProjection).toHaveBeenCalledWith(ids.company, ids.investor, expect.any(AbortSignal));
  });

  it('does not request consolidated projection for a Branch-only Accountant', () => {
    mocks.useAuth.mockReturnValue({
      user: { id: ids.user },
      currentCompany: { id: ids.company, company_wide_roles: [], branches: [{ id: '44444444-4444-4444-8444-444444444444', roles: ['accountant'] }] },
    });
    renderView();
    expect(screen.getByText(/only to a Company-level Accountant/i)).toBeInTheDocument();
    expect(mocks.investorProfitPeriodProjection).not.toHaveBeenCalled();
  });

  it('keeps API failures visible without showing a successful calculation', async () => {
    mocks.investorProfitPeriodProjection.mockRejectedValue(new Error('Forbidden'));
    renderView();
    expect(await screen.findByRole('alert')).toHaveTextContent(/calculation is unavailable/i);
    expect(screen.queryByText('₹1,00,000.00')).not.toBeInTheDocument();
  });

  it('confirms a period only after the server accepts the audited reconciliation', async () => {
    const user = userEvent.setup();
    renderView();
    await screen.findByText('NOT RECONCILED');
    await user.type(screen.getByLabelText('Reason for reconciliation starting 15 Jan 2026'), 'Reviewed source totals');
    await user.click(screen.getByRole('button', { name: 'Confirm period' }));

    await waitFor(() => expect(mocks.reconcileInvestorProfitPeriod).toHaveBeenCalledWith(
      ids.company,
      ids.user,
      ids.investor,
      {
        period_start: '2026-01-15',
        expected_source_version: 'a'.repeat(64),
        reason: 'Reviewed source totals',
      },
    ));
    expect(await screen.findByText('RECONCILED · v1')).toBeInTheDocument();
    expect(screen.getByText(/Position \(not payable\):/)).toBeInTheDocument();
    expect(screen.getByText(/does not create a payable/i)).toBeInTheDocument();
  });

  it('does not show a reconciled status when the confirmation API fails', async () => {
    const user = userEvent.setup();
    mocks.reconcileInvestorProfitPeriod.mockRejectedValue(new Error('Source changed; refresh and review.'));
    renderView();
    await screen.findByText('NOT RECONCILED');
    await user.type(screen.getByLabelText('Reason for reconciliation starting 15 Jan 2026'), 'Reviewed source totals');
    await user.click(screen.getByRole('button', { name: 'Confirm period' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Source changed; refresh and review.');
    expect(screen.getByText('NOT RECONCILED')).toBeInTheDocument();
    expect(screen.queryByText(/RECONCILED · v1/)).not.toBeInTheDocument();
  });

  it('links a login ID and shows access only after the request succeeds', async () => {
    const user = userEvent.setup();
    let activeBinding: {
      id: string; investor_id: string; account_id: string; login_id: string;
      effective_from: string; effective_until: string | null;
    } | null = null;
    mocks.investorPortalBinding.mockImplementation(async () => activeBinding);
    mocks.bindInvestorPortalAccount.mockImplementation(async (_company, _user, investorId, loginId) => {
      activeBinding = {
        id: '55555555-5555-4555-8555-555555555555', investor_id: investorId,
        account_id: ids.user, login_id: loginId, effective_from: '2026-11-19T00:00:00Z', effective_until: null,
      };
      return activeBinding;
    });
    renderView();
    const input = await screen.findByLabelText('Verified login ID');
    await user.type(input, 'investor.login');
    await user.click(screen.getByRole('button', { name: 'Link Investor login' }));
    await waitFor(() => expect(mocks.bindInvestorPortalAccount).toHaveBeenCalledWith(ids.company, ids.user, ids.investor, 'investor.login'));
    expect(await screen.findByText('Active account: investor.login')).toBeInTheDocument();
  });

  it('does not claim revocation success when the API rejects it', async () => {
    const user = userEvent.setup();
    mocks.investorPortalBinding.mockResolvedValue({
      id: '55555555-5555-4555-8555-555555555555', investor_id: ids.investor,
      account_id: ids.user, login_id: 'investor.login', effective_from: '2026-11-19T00:00:00Z', effective_until: null,
    });
    mocks.revokeInvestorPortalBinding.mockRejectedValue(new Error('Permission denied'));
    renderView();
    await screen.findByText('Active account: investor.login');
    await user.type(screen.getByLabelText('Reason to revoke'), 'Account reassigned');
    await user.click(screen.getByRole('button', { name: 'Revoke access' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Permission denied');
    expect(screen.getByText('Active account: investor.login')).toBeInTheDocument();
  });
});
