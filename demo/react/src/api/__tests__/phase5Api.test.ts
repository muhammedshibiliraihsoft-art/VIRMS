import { beforeEach, describe, expect, it, vi } from 'vitest';
import { phase5Api, phase5Mutation } from '../phase5Api';
import { requestApi } from '../client';

vi.mock('../client', () => ({ requestApi: vi.fn() }));

const requestMock = vi.mocked(requestApi);
const ids = {
  user: '11111111-1111-4111-8111-111111111111',
  company: '22222222-2222-4222-8222-222222222222',
  branch: '33333333-3333-4333-8333-333333333333',
  vehicle: '44444444-4444-4444-8444-444444444444',
  sale: '55555555-5555-4555-8555-555555555555',
};

beforeEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
  requestMock.mockResolvedValue({ id: ids.sale });
});

describe('Phase 5 API contracts', () => {
  it('validates the notice-extension response before accepting success', async () => {
    const result = { id: ids.sale, version: 1, previous_deadline: '2027-02-19T00:00:00Z',
      deadline: '2027-04-19T00:00:00Z', reason: 'Vehicle remains open' };
    requestMock.mockResolvedValueOnce(result);
    await expect(phase5Api.extendInvestorExitNotice(ids.company, ids.user, ids.vehicle, ids.sale,
      '2027-04-19T00:00:00Z', 'Vehicle remains open')).resolves.toMatchObject({ id: ids.sale });
    requestMock.mockResolvedValueOnce({ ...result, deadline: '2027-03-19T00:00:00Z' });
    await expect(phase5Api.extendInvestorExitNotice(ids.company, ids.user, ids.vehicle, ids.sale,
      '2027-04-19T00:00:00Z', 'Vehicle remains open')).rejects.toThrow('response could not be verified');
  });
  it('reads the pending cancellation reason and sends an authorized review command', async () => {
    const item = {
      id: ids.sale, status: 'CANCELLATION_PENDING', requested_at: '2026-11-19T00:00:00Z',
      notice_deadline: '2027-02-19T00:00:00Z', history: [
        { version: 1, action: 'SUBMITTED', reason: '' },
        { version: 2, action: 'CANCELLATION_REQUESTED', reason: 'Plans changed' },
      ],
    };
    requestMock.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [item] });
    expect((await phase5Api.investorExitRequests(ids.company, ids.vehicle)).results[0].cancellation_reason).toBe('Plans changed');
    requestMock.mockResolvedValueOnce({ ...item, status: 'CANCELLED' });
    const result = await phase5Api.reviewInvestorExitCancellation(ids.company, ids.user, ids.vehicle, ids.sale, true, ' Approved ');
    expect(result.status).toBe('CANCELLED');
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/investors/${ids.vehicle}/exit-requests/${ids.sale}/cancellation-review/`,
      { method: 'POST', body: { approve: true, reason: 'Approved' }, headers: { 'Idempotency-Key': expect.any(String) } },
    );
    requestMock.mockResolvedValueOnce({ ...item, status: 'REQUESTED' });
    await expect(phase5Api.reviewInvestorExitCancellation(ids.company, ids.user, ids.vehicle, ids.sale, true, '')).rejects.toThrow('response could not be verified');
  });
  it('validates Company-scoped Exit settlement review data', async () => {
    requestMock.mockResolvedValueOnce({
      investor_id: ids.vehicle, exit_request_id: ids.sale, notice_deadline: '2027-02-19T00:00:00Z',
      principal_available: '9000.00', residual_confirmed_loss: '250.00', vehicles: [],
      confirmed_positions: [], confirmed_losses: [], blockers: ['BUYER_PRINCIPAL_REFUND_OPEN'],
      settlement_order: ['PRINCIPAL', 'RESIDUAL_LOSS', 'REMAINING_PROFIT', 'CLOSE'],
      closure_implemented: false, source_version: 'a'.repeat(64),
    });
    const result = await phase5Api.investorExitSettlementPosition(ids.company, ids.vehicle, ids.sale);
    expect(result.blockers).toEqual(['BUYER_PRINCIPAL_REFUND_OPEN']);
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/investors/${ids.vehicle}/exit-requests/${ids.sale}/settlement/`,
      { signal: undefined },
    );
    requestMock.mockResolvedValueOnce({
      investor_id: ids.vehicle, exit_request_id: ids.sale, notice_deadline: '2027-02-19T00:00:00Z',
      principal_available: '9000.00', residual_confirmed_loss: '250.00', vehicles: [],
      confirmed_positions: [], confirmed_losses: [], blockers: [], settlement_order: ['PRINCIPAL'],
      closure_implemented: false, source_version: 'invalid',
    });
    await expect(phase5Api.investorExitSettlementPosition(ids.company, ids.vehicle, ids.sale))
      .rejects.toThrow('Invalid Investor Exit settlement position.');
  });
  it('posts an idempotent partial Exit principal payment with the reviewed source version', async () => {
    const result = { id: ids.sale, investor_id: ids.vehicle, exit_request_id: ids.sale, branch_id: ids.branch,
      amount: '250.00', reference: ' Bank 123 ', effective_at: '2026-11-19T10:00:00Z', allocations: [] };
    requestMock.mockResolvedValueOnce({ ...result, reference: 'Bank 123' });
    await expect(phase5Api.recordInvestorExitPrincipalPayment(ids.company, ids.user, ids.vehicle, ids.sale, {
      branch_id: ids.branch, account_id: ids.user, amount: '250.00', reference: ' Bank 123 ',
      effective_at: '2026-11-19T10:00:00Z', expected_source_version: 'a'.repeat(64), reason: 'Exit partial payment',
    })).resolves.toMatchObject({ amount: '250.00', exit_request_id: ids.sale });
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/investors/${ids.vehicle}/exit-requests/${ids.sale}/principal-payments/`,
      { method: 'POST', body: { branch_id: ids.branch, account_id: ids.user, amount: '250.00', reference: 'Bank 123',
        effective_at: '2026-11-19T10:00:00Z', expected_source_version: 'a'.repeat(64), reason: 'Exit partial payment' },
        headers: { 'Idempotency-Key': expect.any(String) } },
    );
  });
  it('posts a typed Accountant Exit Loss application against the reviewed source version', async () => {
    requestMock.mockResolvedValueOnce({ id: ids.sale, exit_request_id: ids.sale, loss_result_id: ids.vehicle,
      source: 'DIRECT_RECEIPT', amount: '125.00', accounting_event_id: ids.branch, allocations: [] });
    await expect(phase5Api.recordInvestorExitLossApplication(ids.company, ids.user, ids.vehicle, ids.sale, {
      loss_result_id: ids.vehicle, branch_id: ids.branch, account_id: ids.user, source: 'DIRECT_RECEIPT',
      amount: '125.00', effective_at: '2026-11-19T10:00:00Z', expected_source_version: 'a'.repeat(64), reason: 'Exit Loss receipt',
    })).resolves.toMatchObject({ amount: '125.00', source: 'DIRECT_RECEIPT' });
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/investors/${ids.vehicle}/exit-requests/${ids.sale}/loss-applications/`,
      { method: 'POST', body: { loss_result_id: ids.vehicle, branch_id: ids.branch, account_id: ids.user,
        source: 'DIRECT_RECEIPT', amount: '125.00', effective_at: '2026-11-19T10:00:00Z',
        expected_source_version: 'a'.repeat(64), reason: 'Exit Loss receipt' }, headers: { 'Idempotency-Key': expect.any(String) } },
    );
  });
  it('allowlists Investor Vehicle portal fields and drops internal cost and Buyer balances', async () => {
    requestMock.mockResolvedValueOnce({
      investor_id: ids.vehicle,
      name: 'Own Investor',
      binding_id: ids.sale,
      fund_position: {
        credit_total: '0.00', principal_return_total: '0.00', committed_vehicle_total: '0.00',
        use_adjustment_total: '0.00', ledger_available_amount: '0.00',
        withdrawal_eligible: false, status: 'PHASE8_RECONCILIATION_REQUIRED',
      },
      vehicles: [{
        vehicle_id: ids.vehicle, registration: 'KL 11 P 5050', model: 'Hatchback', branch_name: 'Central',
        sale_status: 'NOT_SOLD', confirmed_result_status: 'NOT_CONFIRMED',
        purchase_cost: '30000.00', vehicle_expense_cost: '1000.00', total_vehicle_cost: '31000.00',
        investor_share_percentage_snapshot: '33.0000', sale_price: '40000.00',
        actual_net_collection: '20000.00', buyer_receivable: '20000.00', buyer_refund_payable: '0.00',
      }],
      interim: { status: 'NOT_CONFIGURED', monthly_amount: null, effective_date: null, payout_status: 'NOT_RECONCILED' },
      profit_calendar: { status: 'NOT_AVAILABLE', start_date: null, duration_months: null, source: null },
      profit_period_status: 'RECONCILED', unassigned_result_count: 0,
      profit_periods: [{
        period_start: '2026-01-15', period_end: '2026-07-14', duration_months: 6,
        gross_investor_profit: '1000.00', investor_loss_share: '250.00',
        deal_profit_paid: '300.00', interim_paid: '200.00', loss_offset_applied: '100.00',
        result_count: 2, status: 'CALCULATED_NOT_RECONCILED', paid_status: 'NOT_RECONCILED',
        reconciliation_status: 'RECONCILED',
        confirmed_snapshot: {
          version: 1, confirmed_at: '2026-07-15T10:00:00Z',
          gross_investor_profit: '1000.00', investor_loss_share: '250.00',
          deal_profit_paid: '300.00', interim_paid: '200.00', loss_offset_applied: '100.00',
          net_position: '400.00', restatement_adjustment: '0.00',
          pending_restatement_adjustment: null,
          notice: 'Confirmed calculation snapshot only; not a payable, payment, or final settlement.',
          source_version: 'private-source-fingerprint', reason: 'private Accountant reason',
          confirmed_by_id: ids.user,
        },
      }], vehicle_results: [{
        vehicle_id: ids.vehicle, sale_id: ids.sale, effective_sale_date: '2026-06-01',
        status: 'CURRENT', result_kind: 'PROFIT', investor_share_amount: '1000.00',
        deal_profit_paid: '300.00', loss_offset_applied: '100.00',
        interim_paid: '0.00',
        confirmed_at: '2026-06-01T10:00:00Z', current: true,
      }], exit_requests: [],
    });

    const result = await phase5Api.investorPortalSelf(ids.company);

    expect(result.vehicles[0]).toEqual({
      vehicle_id: ids.vehicle, registration: 'KL 11 P 5050', model: 'Hatchback',
      branch_name: 'Central', sale_status: 'NOT_SOLD', confirmed_result_status: 'NOT_CONFIRMED',
    });
    expect(result.vehicle_results[0].loss_offset_applied).toBe('100.00');
    expect(result.profit_periods[0]?.confirmed_snapshot?.net_position).toBe('400.00');
    expect(result.profit_periods[0]?.confirmed_snapshot).not.toHaveProperty('source_version');
    expect(result.profit_periods[0]?.confirmed_snapshot).not.toHaveProperty('reason');
    expect(result.profit_periods[0]?.confirmed_snapshot).not.toHaveProperty('confirmed_by_id');
  });

  it('reads only typed, allowlisted pages of the bound Investor Fund history', async () => {
    requestMock.mockResolvedValueOnce({
      count: 1, next: null, previous: null,
      results: [{
        id: ids.sale, effective_at: '2026-05-03T09:00:00Z', amount: '-30000.00',
        activity_type: 'VEHICLE_COMMITMENT', branch_name: 'Central',
        vehicle_registration: 'KL 11 P 5050', reference: 'PRIVATE-BANK-REFERENCE',
        other_investor_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      }],
    });

    const result = await phase5Api.investorPortalFundHistory(ids.company, 1);

    expect(result).toEqual({
      count: 1, next: null, previous: null,
      results: [{
        id: ids.sale, effective_at: '2026-05-03T09:00:00Z', amount: '-30000.00',
        activity_type: 'VEHICLE_COMMITMENT', branch_name: 'Central',
        vehicle_registration: 'KL 11 P 5050',
      }],
    });
    expect(requestMock).toHaveBeenCalledWith(
      `tenants/${ids.company}/investment/portal/self/fund-history/?page=1`,
      { signal: undefined },
    );
  });

  it('rejects invalid Fund history pages and malformed activity fields', async () => {
    expect(() => phase5Api.investorPortalFundHistory(ids.company, 0)).toThrow(/positive integer/i);
    requestMock.mockResolvedValueOnce({
      count: 1, next: null, previous: null,
      results: [{
        id: ids.sale, effective_at: '2026-05-03T09:00:00Z', amount: '3.00',
        activity_type: 'COMPANY_BANK_BALANCE', branch_name: 'Central', vehicle_registration: null,
      }],
    });
    await expect(phase5Api.investorPortalFundHistory(ids.company, 1)).rejects.toThrow(/Invalid Investor Fund activity/i);
  });

  it('accepts only unavailable Fund totals while an attribution correction needs manual review', async () => {
    requestMock.mockResolvedValueOnce({
      investor_id: ids.vehicle, name: 'Own Investor', binding_id: ids.sale,
      fund_position: {
        credit_total: null, principal_return_total: null, committed_vehicle_total: null,
        use_adjustment_total: null, ledger_available_amount: null, withdrawal_eligible: false,
        status: 'MANUAL_REVIEW_REQUIRED', internal_cash_account_id: ids.branch,
      },
      vehicles: [], interim: { status: 'NOT_CONFIGURED', monthly_amount: null, effective_date: null, payout_status: 'NOT_RECONCILED' },
      profit_calendar: { status: 'NOT_AVAILABLE', start_date: null, duration_months: null, source: null },
      profit_period_status: 'MANUAL_REVIEW_REQUIRED', unassigned_result_count: 0,
      profit_periods: [], vehicle_results: [], exit_requests: [],
    });

    const result = await phase5Api.investorPortalSelf(ids.company);

    expect(result.fund_position).toEqual({
      credit_total: null, principal_return_total: null, committed_vehicle_total: null,
      use_adjustment_total: null, ledger_available_amount: null, withdrawal_eligible: false,
      status: 'MANUAL_REVIEW_REQUIRED',
    });
    expect(result.fund_position).not.toHaveProperty('internal_cash_account_id');
  });

  it('reads a typed Company Accountant Investor period calculation without accepting malformed money', async () => {
    requestMock.mockResolvedValueOnce({
      company_id: ids.company,
      investor_id: ids.vehicle,
      calendar: { status: 'CONFIGURED', start_date: '2026-01-15', duration_months: 6, versions: [] },
      status: 'CALCULATED_NOT_RECONCILED',
      periods: [{
        period_start: '2026-01-15', period_end: '2026-07-14', duration_months: 6,
        gross_investor_profit: '100.00', investor_loss_share: '5.00',
        deal_profit_paid: '25.00', loss_offset_applied: '3.00',
        interim_paid: '12.00',
        result_count: 1, status: 'CALCULATED_NOT_RECONCILED', paid_status: 'NOT_RECONCILED',
        source_version: 'a'.repeat(64), reconciliation_status: 'NOT_RECONCILED',
        reconciliation_id: null, reconciliation_version: null,
        last_reconciled_net_position: null, last_restatement_adjustment: null,
        pending_restatement_adjustment: null,
      }],
      unassigned_result_count: 0,
      settlement_status: 'NOT_IMPLEMENTED',
      notice: 'Calculation only.',
    });
    const result = await phase5Api.investorProfitPeriodProjection(ids.company, ids.vehicle);
    expect(result.periods[0]?.gross_investor_profit).toBe('100.00');
    expect(result.periods[0]?.deal_profit_paid).toBe('25.00');
    expect(result.periods[0]?.interim_paid).toBe('12.00');
    expect(result.periods[0]?.loss_offset_applied).toBe('3.00');
    expect(result.periods[0]).not.toHaveProperty('calculated_unpaid_profit');
    expect(requestMock).toHaveBeenCalledWith(
      `tenants/${ids.company}/investment/investors/${ids.vehicle}/profit-periods/`,
      { signal: undefined },
    );

    requestMock.mockResolvedValueOnce({
      company_id: ids.company,
      investor_id: ids.vehicle,
      calendar: { status: 'CONFIGURED', start_date: '2026-01-15', duration_months: 6, versions: [] },
      status: 'CALCULATED_NOT_RECONCILED',
      periods: [{
        period_start: '2026-01-15', period_end: '2026-07-14', duration_months: 6,
        gross_investor_profit: 'NaN', investor_loss_share: '5.00',
        deal_profit_paid: '0.00', loss_offset_applied: '0.00',
        interim_paid: '0.00',
        result_count: 1, status: 'CALCULATED_NOT_RECONCILED', paid_status: 'NOT_RECONCILED',
        source_version: 'a'.repeat(64), reconciliation_status: 'NOT_RECONCILED',
        reconciliation_id: null, reconciliation_version: null,
        last_reconciled_net_position: null, last_restatement_adjustment: null,
        pending_restatement_adjustment: null,
      }],
      unassigned_result_count: 0,
      settlement_status: 'NOT_IMPLEMENTED',
      notice: 'Calculation only.',
    });
    await expect(phase5Api.investorProfitPeriodProjection(ids.company, ids.vehicle)).rejects.toThrow(/Invalid Investor Profit gross_investor_profit/);
  });

  it('posts a typed audited period reconciliation with a safe idempotency key', async () => {
    const response = {
      id: ids.sale,
      investor_id: ids.vehicle,
      period_start: '2026-01-15',
      period_end: '2026-07-14',
      duration_months: 6,
      result_count: 1,
      version: 1,
      source_version: 'a'.repeat(64),
      gross_investor_profit: '100.00',
      investor_loss_share: '5.00',
      deal_profit_paid: '25.00',
      interim_paid: '12.00',
      loss_offset_applied: '3.00',
      net_position: '60.00',
      restatement_adjustment: '0.00',
      previous_reconciliation_id: null,
      reason: 'Reviewed the period',
      confirmed_at: '2026-07-15T10:00:00Z',
      confirmed_by_id: ids.user,
    };
    const body = {
      period_start: '2026-01-15',
      expected_source_version: 'a'.repeat(64),
      reason: '  Reviewed the period  ',
    };
    requestMock.mockResolvedValueOnce(response);

    const result = await phase5Api.reconcileInvestorProfitPeriod(ids.company, ids.user, ids.vehicle, body);

    expect(result).toEqual(response);
    expect(requestMock).toHaveBeenCalledWith(
      'tenants/' + ids.company + '/investment/investors/' + ids.vehicle + '/profit-period-reconciliations/',
      {
        method: 'POST',
        body: { ...body, reason: 'Reviewed the period' },
        headers: { 'Idempotency-Key': expect.any(String) },
      },
    );
  });

  it('reads a paginated Investor-only Interim payment history', async () => {
    requestMock.mockResolvedValueOnce({
      count: 1, next: null, previous: null,
      results: [{ id: ids.sale, period_month: '2026-10-01', effective_at: '2026-10-10T12:00:00Z', amount: '400.00' }],
    });
    const page = await phase5Api.investorPortalInterimPaymentHistory(ids.company, 1);
    expect(page.results[0]?.amount).toBe('400.00');
    expect(requestMock).toHaveBeenCalledWith(
      `tenants/${ids.company}/investment/portal/self/interim-payment-history/?page=1`,
      { signal: undefined },
    );
    expect(() => phase5Api.investorPortalInterimPaymentHistory(ids.company, 0)).toThrow(/page must be a positive integer/i);
  });

  it('posts a typed Investor Vehicle Profit payment with the current confirmed result as its source', async () => {
    const accountId = '77777777-7777-4777-8777-777777777777';
    const eventId = '88888888-8888-4888-8888-888888888888';
    const movementId = '99999999-9999-4999-8999-999999999999';
    const response = {
      payment_id: ids.sale,
      result_confirmation_id: ids.vehicle,
      investor_id: ids.vehicle,
      vehicle_id: ids.vehicle,
      sale_id: ids.sale,
      branch_id: ids.branch,
      account_id: accountId,
      amount: '250.00',
      paid_total: '250.00',
      remaining_share: '450.00',
      effective_at: '2026-11-19T10:00:00Z',
      accounting_event_id: eventId,
      movement_id: movementId,
    };
    requestMock.mockResolvedValueOnce(response);
    const input = { account_id: accountId, amount: '250.00', effective_at: '2026-11-19T10:00:00Z' };

    const result = await phase5Api.recordInvestorVehicleProfitPayment(
      ids.company, ids.user, ids.sale, input,
    );

    expect(result.payment_id).toBe(ids.sale);
    expect(requestMock).toHaveBeenCalledWith(
      `tenants/${ids.company}/investment/vehicle-results/${ids.sale}/profit-payments/`,
      expect.objectContaining({
        method: 'POST',
        body: input,
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
  });

  it('reads and records only typed Investor Loss offset options and facts', async () => {
    const profitResultId = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
    requestMock.mockResolvedValueOnce({
      loss_result_id: ids.sale,
      loss_remaining_amount: '800.00',
      target_options: [{
        result_id: profitResultId, vehicle_id: ids.vehicle, registration: 'KL 11 P 6060',
        model: 'Sedan', sale_branch_id: ids.branch, sale_date: '2026-11-18',
        investor_share_amount: '1000.00', remaining_amount: '700.00',
      }],
    });
    const options = await phase5Api.investorProfitLossOffsetOptions(ids.company, ids.sale);
    expect(options.loss_remaining_amount).toBe('800.00');
    expect(options.target_options[0].remaining_amount).toBe('700.00');
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/vehicle-results/${ids.sale}/profit-loss-offsets/`,
      { signal: undefined },
    );

    requestMock.mockResolvedValueOnce({
      offset_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
      loss_result_id: ids.sale, profit_result_id: profitResultId,
      investor_id: ids.vehicle, branch_id: ids.branch,
      amount: '300.00', loss_remaining: '500.00', profit_remaining: '400.00',
      effective_at: '2026-11-19T10:00:00Z', reason: 'Apply reviewed loss',
    });
    const posted = await phase5Api.recordInvestorProfitLossOffset(
      ids.company, ids.user, ids.sale,
      { profit_result_id: profitResultId, amount: '300.00', reason: 'Apply reviewed loss' },
    );
    expect(posted).toMatchObject({ amount: '300.00', profit_remaining: '400.00' });
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/vehicle-results/${ids.sale}/profit-loss-offsets/`,
      expect.objectContaining({
        method: 'POST',
        body: { profit_result_id: profitResultId, amount: '300.00', reason: 'Apply reviewed loss' },
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
  });

  it('reads and mutates Investor portal bindings through the Company-scoped API', async () => {
    const binding = {
      id: ids.sale, investor_id: ids.vehicle, account_id: ids.user,
      login_id: 'investor.login', effective_from: '2026-11-19T00:00:00Z', effective_until: null,
    };
    requestMock.mockResolvedValueOnce(null);
    expect(await phase5Api.investorPortalBinding(ids.company, ids.vehicle)).toBeNull();
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/investors/${ids.vehicle}/portal-binding/`,
      { signal: undefined },
    );

    requestMock.mockResolvedValueOnce(binding);
    const created = await phase5Api.bindInvestorPortalAccount(ids.company, ids.user, ids.vehicle, ' investor.login ');
    expect(created).toMatchObject({ id: ids.sale, login_id: 'investor.login' });
    expect(requestMock).toHaveBeenLastCalledWith(
      `tenants/${ids.company}/investment/investors/${ids.vehicle}/portal-binding/`,
      { method: 'POST', body: { login_id: 'investor.login' }, headers: { 'Idempotency-Key': expect.any(String) } },
    );

    requestMock.mockResolvedValueOnce({ ...binding, effective_until: '2026-11-20T00:00:00Z' });
    expect(await phase5Api.revokeInvestorPortalBinding(ids.company, ids.user, ids.sale, 'Role ended')).toMatchObject({ effective_until: '2026-11-20T00:00:00Z' });
  });

  it('requires a valid server-calculated Running Capital total on expense lists', async () => {
    requestMock.mockResolvedValueOnce({ count: 21, next: '?page=2', previous: null, results: [], running_capital_total: '2150.00' });
    expect((await phase5Api.expenses(ids.company, ids.vehicle, { page: 1 })).running_capital_total).toBe('2150.00');
    requestMock.mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] });
    await expect(phase5Api.expenses(ids.company, ids.vehicle)).rejects.toThrow('Invalid Vehicle Expense Running Capital total response.');
  });
  it('accepts null receivable and refund balances when a Vehicle has no Sale yet', async () => {
    requestMock.mockResolvedValueOnce({
      vehicle_id: ids.vehicle,
      company_id: ids.company,
      branch_id: ids.branch,
      purchase_id: ids.sale,
      sale_id: null,
      investor_id: null,
      investor_share_agreement_id: null,
      investor_share_percentage_snapshot: null,
      profit_share_status: 'NOT_APPLICABLE',
      purchase_cost: '100000.00',
      vehicle_expense_cost: '5000.00',
      total_vehicle_cost: '105000.00',
      investor_fund_cost: '70000.00',
      running_capital_cost: '35000.00',
      sale_price: null,
      actual_net_collection: '0.00',
      buyer_receivable: null,
      buyer_refund_payable: null,
      calculated_result: null,
      status: 'NOT_SOLD',
      settlement_eligible: false,
      source_version: 'a'.repeat(64),
      confirmed_result: null,
      purchase_correction_version: 0,
      expense_correction_versions: [],
      sale_correction_version: 0,
    });

    const result = await phase5Api.vehicleFinancialPosition(ids.company, ids.vehicle);

    expect(result.sale_id).toBeNull();
    expect(result.buyer_receivable).toBeNull();
    expect(result.buyer_refund_payable).toBeNull();
  });
  it('reads typed Vehicle Sale data and exposes whether its source uses Investor Fund', async () => {
    requestMock.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: ids.sale,
        company_id: ids.company,
        vehicle_id: ids.vehicle,
        vehicle_registration: 'KL 11 P 5050',
        vehicle_model: 'Hatchback',
        branch_id: ids.branch,
        branch_name: 'Central',
        sale_price: '12000.00',
        investor_funded: true,
        buyer_name: 'Maya',
        buyer_phone: '9876543210',
        sold_at: '2026-11-11T08:00:00Z',
        received_total: '2000.00',
        refunded_total: '0.00',
        net_received: '2000.00',
        receivable: '10000.00',
        refund_available: '2000.00',
        correction_version: 0,
        receipts: [],
        refunds: [{ id: ids.vehicle, account_id: ids.branch, amount: '500.00', effective_at: '2026-11-11T09:00:00Z' }],
      }],
    });

    const result = await phase5Api.sales(ids.company, { page: 1, branchId: ids.branch });

    expect(result.results[0]?.investor_funded).toBe(true);
    expect(result.results[0]?.refunds[0]?.amount).toBe('500.00');
    expect(requestMock).toHaveBeenCalledWith(
      `tenants/${ids.company}/vehicle-management/sales/?page=1&branch_id=${ids.branch}`,
      { signal: undefined },
    );
  });

  it('validates typed Sale price-correction history', async () => {
    requestMock.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: ids.sale,
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
        received_total: '0.00',
        refunded_total: '0.00',
        net_received: '0.00',
        receivable: '11000.00',
        refund_payable: '0.00',
        refund_available: '0.00',
        correction_version: 1,
        receipts: [],
        refunds: [],
        corrections: [{
          id: ids.vehicle,
          version: 1,
          previous_sale_price: '12000.00',
          sale_price: '11000.00',
          reason: 'Signed amount corrected.',
          effective_at: '2026-11-11T08:00:00Z',
          recorded_at: '2026-11-12T08:00:00Z',
        }],
      }],
    });

    const result = await phase5Api.sales(ids.company, { page: 1 });

    expect(result.results[0]?.corrections[0]).toMatchObject({
      previous_sale_price: '12000.00',
      sale_price: '11000.00',
      reason: 'Signed amount corrected.',
    });
    expect(result.results[0]?.corrections[0]?.recorded_at).toBe('2026-11-12T08:00:00Z');

    requestMock.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: ids.sale,
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
        received_total: '0.00',
        refunded_total: '0.00',
        net_received: '0.00',
        receivable: '11000.00',
        refund_payable: '0.00',
        refund_available: '0.00',
        correction_version: 1,
        receipts: [],
        refunds: [],
        corrections: [{ id: 'invalid-id' }],
      }],
    });

    await expect(phase5Api.sales(ids.company, { page: 1 })).rejects.toThrow('Invalid Sale correction id response.');
  });

  it('parses typed Fund Credit attribution correction history and manual-review state', async () => {
    const investor = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
    const correctedInvestor = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
    requestMock.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: ids.sale,
        investor_id: correctedInvestor,
        original_investor_id: investor,
        branch_id: ids.branch,
        amount: '50000.00',
        reference: 'FUND-REF-1',
        effective_at: '2026-10-01T00:00:00Z',
        recorded_at: '2026-10-01T00:00:00Z',
        accounting_event_id: ids.sale,
        correction_version: 1,
        manual_review_required: true,
        attribution_corrections: [{
          id: ids.vehicle,
          from_investor_id: investor,
          to_investor_id: correctedInvestor,
          amount: '50000.00',
          effective_at: '2026-10-01T00:00:00Z',
          recorded_at: '2026-11-11T00:00:00Z',
          reason: 'Wrong Investor attribution.',
        }],
      }],
    });

    const result = await phase5Api.fundCredits(ids.company, { page: 1 });

    expect(result.results[0]?.investor_id).toBe(correctedInvestor);
    expect(result.results[0]?.manual_review_required).toBe(true);
    expect(result.results[0]?.attribution_corrections[0]?.reason).toBe('Wrong Investor attribution.');
  });

  it('rejects malformed typed records instead of exposing partial values to the UI', async () => {
    requestMock.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [{ id: 'not-a-uuid' }],
    });

    await expect(phase5Api.vehicles(ids.company, { page: 1 })).rejects.toThrow('Invalid Vehicle id response.');
  });
});

describe('Phase 5 mutation idempotency', () => {
  it('reuses the same key after an ambiguous network failure', async () => {
    requestMock.mockRejectedValueOnce(new Error('network failure'));
    const body = { vehicle_id: ids.vehicle, amount: '125.50' };

    await expect(phase5Mutation(ids.company, ids.user, 'vehicle-management', 'vehicles/x/expenses/', body))
      .rejects.toThrow('network failure');
    await phase5Mutation(ids.company, ids.user, 'vehicle-management', 'vehicles/x/expenses/', body);

    const firstHeaders = requestMock.mock.calls[0][1]?.headers as Record<string, string>;
    const retryHeaders = requestMock.mock.calls[1][1]?.headers as Record<string, string>;
    expect(firstHeaders['Idempotency-Key']).toBeTruthy();
    expect(retryHeaders['Idempotency-Key']).toBe(firstHeaders['Idempotency-Key']);
  });

  it('does not send a financial mutation if retry-key storage is unavailable', async () => {
    vi.stubGlobal('sessionStorage', {
      getItem: () => null,
      setItem: () => { throw new DOMException('Storage is disabled.', 'SecurityError'); },
      removeItem: vi.fn(),
    });

    await expect(phase5Mutation(ids.company, ids.user, 'investment', 'fund/credits/', { amount: '100.00' }))
      .rejects.toThrow('safe retry storage is unavailable');
    expect(requestMock).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});
