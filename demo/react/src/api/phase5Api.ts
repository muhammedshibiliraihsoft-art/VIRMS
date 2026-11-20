import { ApiMethod, requestApi } from './client';

export interface ApiPage<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ExpensePage extends ApiPage<Phase5Expense> {
  running_capital_total: string;
}

export interface Phase5Investor {
  id: string;
  company_id: string;
  name: string;
  is_active: boolean;
}

export interface Phase5ProfitCalendarConfiguration {
  id: string;
  investor_id: string;
  effective_start: string;
  duration_months: number;
  version: number;
  recorded_at: string;
  actor_id: string;
}

export interface InvestorPortalBinding {
  id: string;
  investor_id: string;
  account_id: string;
  login_id: string;
  effective_from: string;
  effective_until: string | null;
}

export interface InvestorExitNotice {
  id: string;
  status: 'REQUESTED' | 'CANCELLATION_PENDING' | 'CANCELLED' | 'SETTLED';
  requested_at: string;
  notice_deadline: string;
  cancellation_reason: string | null;
}

export interface InvestorExitSettlementPosition {
  investor_id: string;
  exit_request_id: string;
  notice_deadline: string;
  principal_available: string | null;
  residual_confirmed_loss: string;
  vehicles: Array<{ vehicle_id: string; label: string; source_version: string; status: string }>;
  confirmed_positions: Array<{ id: string; kind: 'PAYABLE' | 'RECOVERABLE' | 'BALANCED'; amount: string; source_version: string; is_current: boolean; period_start: string; period_end: string }>;
  confirmed_losses: Array<{ loss_result_id: string; vehicle_id: string; label: string; amount: string }>;
  blockers: string[];
  settlement_order: string[];
  closure_implemented: boolean;
  settlement_status?: string;
  source_version: string;
}

function parseInvestorExitSettlementPosition(value: unknown): InvestorExitSettlementPosition {
  const row = requireRecord(value, 'Investor Exit settlement position');
  requireUuid(row.investor_id, 'Investor id');
  requireUuid(row.exit_request_id, 'Investor Exit request id');
  if (typeof row.notice_deadline !== 'string' || Number.isNaN(Date.parse(row.notice_deadline)) ||
      (row.principal_available !== null && typeof row.principal_available !== 'string') ||
      typeof row.residual_confirmed_loss !== 'string' || !Array.isArray(row.vehicles) ||
      !Array.isArray(row.confirmed_positions) || !Array.isArray(row.confirmed_losses) || !Array.isArray(row.blockers) ||
      !row.blockers.every((item) => typeof item === 'string') || !Array.isArray(row.settlement_order) ||
      !row.settlement_order.every((item) => typeof item === 'string') ||
      typeof row.closure_implemented !== 'boolean' || typeof row.source_version !== 'string' ||
      !/^[0-9a-f]{64}$/.test(row.source_version)) {
    throw new Error('Invalid Investor Exit settlement position.');
  }
  const vehicles = row.vehicles.map((value) => {
    const vehicle = requireRecord(value, 'Investor Exit Vehicle position');
    requireUuid(vehicle.vehicle_id, 'Vehicle id');
    if (typeof vehicle.label !== 'string' || typeof vehicle.source_version !== 'string' ||
        typeof vehicle.status !== 'string') throw new Error('Invalid Investor Exit Vehicle position.');
    return { vehicle_id: vehicle.vehicle_id as string, label: vehicle.label,
      source_version: vehicle.source_version, status: vehicle.status };
  });
  const confirmedLosses = row.confirmed_losses.map((value) => {
    const loss = requireRecord(value, 'Investor Exit Loss position');
    requireUuid(loss.loss_result_id, 'Investor Loss result id');
    requireUuid(loss.vehicle_id, 'Vehicle id');
    if (typeof loss.label !== 'string') throw new Error('Invalid Investor Exit Loss vehicle label.');
    requireMoney(loss.amount, 'Investor Exit Loss amount');
    return { loss_result_id: loss.loss_result_id as string, vehicle_id: loss.vehicle_id as string, label: loss.label, amount: loss.amount as string };
  });
  const confirmedPositions = row.confirmed_positions.map((value) => {
    const position = requireRecord(value, 'Investor Exit confirmed Profit position');
    requireUuid(position.id, 'Confirmed Profit position id');
    if (!['PAYABLE', 'RECOVERABLE', 'BALANCED'].includes(String(position.kind)) ||
        typeof position.source_version !== 'string' || !/^[0-9a-f]{64}$/.test(position.source_version) ||
        typeof position.is_current !== 'boolean' || typeof position.period_start !== 'string' ||
        typeof position.period_end !== 'string') throw new Error('Invalid Investor Exit confirmed Profit position.');
    requireMoney(position.amount, 'Confirmed Profit position amount');
    return { id: position.id as string, kind: position.kind as 'PAYABLE' | 'RECOVERABLE' | 'BALANCED',
      amount: position.amount as string, source_version: position.source_version, is_current: position.is_current,
      period_start: position.period_start, period_end: position.period_end };
  });
  return {
    investor_id: row.investor_id as string, exit_request_id: row.exit_request_id as string,
    notice_deadline: row.notice_deadline, principal_available: row.principal_available as string | null,
    residual_confirmed_loss: row.residual_confirmed_loss, vehicles,
    confirmed_positions: confirmedPositions, confirmed_losses: confirmedLosses, blockers: row.blockers as string[],
    settlement_order: row.settlement_order as string[], closure_implemented: row.closure_implemented,
    settlement_status: row.settlement_status as string,
    source_version: row.source_version,
  };
}

function parseInvestorExitNotice(value: unknown): InvestorExitNotice {
  const row = requireRecord(value, 'Investor Exit notice');
  requireUuid(row.id, 'Investor Exit request id');
  if (!['REQUESTED', 'CANCELLATION_PENDING', 'CANCELLED', 'SETTLED'].includes(String(row.status)) ||
      typeof row.requested_at !== 'string' || Number.isNaN(Date.parse(row.requested_at)) ||
      typeof row.notice_deadline !== 'string' || Number.isNaN(Date.parse(row.notice_deadline))) {
    throw new Error('Invalid Investor Exit notice.');
  }
  if (!Array.isArray(row.history)) throw new Error('Invalid Investor Exit history.');
  const history = row.history.map((item) => {
    const entry = requireRecord(item, 'Investor Exit history');
    if (!Number.isInteger(entry.version) || typeof entry.action !== 'string' || typeof entry.reason !== 'string') {
      throw new Error('Invalid Investor Exit history.');
    }
    return { version: entry.version as number, action: entry.action, reason: entry.reason };
  });
  const latestCancellation = history.filter((entry) => entry.action === 'CANCELLATION_REQUESTED')
    .sort((a, b) => b.version - a.version)[0];
  if (row.status === 'CANCELLATION_PENDING' && !latestCancellation) {
    throw new Error('Pending Exit cancellation has no request history.');
  }
  return { id: row.id as string, status: row.status as InvestorExitNotice['status'],
    requested_at: row.requested_at, notice_deadline: row.notice_deadline,
    cancellation_reason: row.status === 'CANCELLATION_PENDING' ? (latestCancellation?.reason ?? null) : null };
}

export interface InvestorProfitPosition {
  future_profit_recovered?: string;
  future_profit_applied?: string;
  repaid?: string;
  id: string;
  source_version: string;
  kind: 'PAYABLE' | 'RECOVERABLE' | 'BALANCED';
  amount: string;
  is_current: boolean;
  confirmed_at: string;
  reason: string;
}

export interface FutureProfitAdjustmentTarget {
  profit_position_id: string;
  profit_result_id: string;
  source_version: string;
  amount: string;
  label: string;
}

export interface InvestorProfitPeriodProjection {
  company_id: string;
  investor_id: string;
  calendar: {
    status: 'CONFIGURED' | 'SCHEDULED' | 'DEFAULT_FROM_FIRST_FUND_CREDIT' | 'NOT_AVAILABLE';
    start_date: string | null;
    duration_months: number | null;
    versions: Phase5ProfitCalendarConfiguration[];
  };
  status: 'CALENDAR_NOT_AVAILABLE' | 'REVIEW_REQUIRED' | 'CALCULATED_NOT_RECONCILED' | 'RECONCILED';
  periods: Array<{
    future_profit_targets?: FutureProfitAdjustmentTarget[];
    confirmed_position?: InvestorProfitPosition | null;
    period_start: string;
    period_end: string;
    duration_months: number;
    gross_investor_profit: string;
    investor_loss_share: string;
    deal_profit_paid: string;
    interim_paid: string;
    loss_offset_applied: string;
    result_count: number;
    status: 'CALCULATED_NOT_RECONCILED' | 'SOURCE_REVIEW_REQUIRED';
    paid_status: 'NOT_RECONCILED';
    source_version: string | null;
    reconciliation_status: 'NOT_RECONCILED' | 'RECONCILED' | 'RESTATEMENT_REQUIRED' | 'SOURCE_REVIEW_REQUIRED';
    reconciliation_id: string | null;
    reconciliation_version: number | null;
    last_reconciled_net_position: string | null;
    last_restatement_adjustment: string | null;
    pending_restatement_adjustment: string | null;
  }>;
  unassigned_result_count: number;
  settlement_status: 'NOT_IMPLEMENTED';
  notice: string;
}

export interface InvestorProfitPeriodReconciliation {
  id: string;
  investor_id: string;
  period_start: string;
  period_end: string;
  duration_months: number;
  result_count: number;
  version: number;
  source_version: string;
  gross_investor_profit: string;
  investor_loss_share: string;
  deal_profit_paid: string;
  interim_paid: string;
  loss_offset_applied: string;
  net_position: string;
  restatement_adjustment: string;
  previous_reconciliation_id: string | null;
  reason: string;
  confirmed_at: string;
  confirmed_by_id: string;
}

export interface InvestorVehicleProfitPaymentReceipt {
  payment_id: string;
  result_confirmation_id: string;
  investor_id: string;
  vehicle_id: string;
  sale_id: string;
  branch_id: string;
  account_id: string;
  amount: string;
  paid_total: string;
  remaining_share: string;
  effective_at: string;
  accounting_event_id: string;
  movement_id: string;
}

export interface InvestorProfitLossOffsetTarget {
  result_id: string;
  vehicle_id: string;
  registration: string;
  model: string;
  sale_branch_id: string;
  sale_date: string;
  investor_share_amount: string;
  remaining_amount: string;
}

export interface InvestorProfitLossOffsetOptions {
  loss_result_id: string;
  loss_remaining_amount: string;
  target_options: InvestorProfitLossOffsetTarget[];
}

export interface InvestorPortalSnapshot {
  investor_id: string;
  name: string;
  binding_id: string;
  fund_position: {
    credit_total: string | null;
    principal_return_total: string | null;
    committed_vehicle_total: string | null;
    use_adjustment_total: string | null;
    ledger_available_amount: string | null;
    withdrawal_eligible: false;
    status: 'PHASE8_RECONCILIATION_REQUIRED' | 'MANUAL_REVIEW_REQUIRED';
  };
  vehicles: Array<{
    vehicle_id: string;
    registration: string;
    model: string;
    branch_name: string;
    sale_status: string;
    confirmed_result_status: 'CURRENT' | 'STALE_REVIEW_REQUIRED' | 'NOT_CONFIRMED';
    confirmed_result?: {
      result_kind: 'PROFIT' | 'LOSS' | 'BREAK_EVEN';
      investor_share_amount: string;
      deal_profit_paid: string;
      loss_offset_applied: string;
      confirmed_at: string;
      current: boolean;
    };
  }>;
  interim: {
    status: 'CONFIGURED' | 'NOT_CONFIGURED';
    monthly_amount: string | null;
    effective_date: string | null;
    payout_status: 'NOT_RECONCILED';
  };
  profit_calendar: {
    status: 'DEFAULT_FROM_FIRST_FUND_CREDIT' | 'CONFIGURED' | 'SCHEDULED' | 'NOT_AVAILABLE';
    start_date: string | null;
    duration_months: number | null;
    source: 'DEFAULT_SIX_MONTHS' | 'ACCOUNTANT_CONFIGURED' | null;
  };
  profit_period_status: 'MANUAL_REVIEW_REQUIRED' | 'CALENDAR_NOT_AVAILABLE' | 'CALENDAR_NOT_ACTIVE' | 'REVIEW_REQUIRED' | 'CALCULATED_NOT_RECONCILED' | 'RESTATEMENT_REQUIRED' | 'RECONCILED';
  unassigned_result_count: number;
  profit_periods: Array<{
    period_start: string;
    period_end: string;
    duration_months: number;
    gross_investor_profit: string;
    investor_loss_share: string;
    deal_profit_paid: string;
    interim_paid: string;
    loss_offset_applied: string;
    result_count: number;
    status: 'CALCULATED_NOT_RECONCILED' | 'SOURCE_REVIEW_REQUIRED';
    paid_status: 'NOT_RECONCILED';
    reconciliation_status: 'NOT_RECONCILED' | 'RECONCILED' | 'RESTATEMENT_REQUIRED' | 'SOURCE_REVIEW_REQUIRED';
    confirmed_snapshot: {
      version: number;
      confirmed_at: string;
      gross_investor_profit: string;
      investor_loss_share: string;
      deal_profit_paid: string;
      interim_paid: string;
      loss_offset_applied: string;
      net_position: string;
      restatement_adjustment: string;
      pending_restatement_adjustment: string | null;
      notice: string;
    } | null;
  }>;
  vehicle_results: Array<{
    vehicle_id: string;
    sale_id: string | null;
    effective_sale_date: string | null;
    status: string;
    result_kind: 'PROFIT' | 'LOSS' | 'BREAK_EVEN';
    investor_share_amount: string;
    deal_profit_paid: string;
    loss_offset_applied: string;
    confirmed_at: string;
    current: boolean;
  }>;
  exit_requests: Array<{
    id: string;
    status: 'REQUESTED' | 'CANCELLATION_PENDING' | 'CANCELLED';
    terms_version: string;
    terms_accepted_at: string;
    requested_at: string;
    initial_notice_deadline?: string;
    notice_deadline?: string;
    notice_extensions?: Array<{ id: string; version: number; previous_deadline: string; deadline: string; reason: string; recorded_at: string }>;
    history: Array<{ version: number; action: string; previous_status: string | null; new_status: string; reason: string; recorded_at: string }>;
  }>;
}

export interface InvestorFundActivity {
  id: string;
  effective_at: string;
  amount: string;
  activity_type: 'FUND_CREDIT' | 'PRINCIPAL_RETURN' | 'VEHICLE_COMMITMENT' | 'COMMITMENT_ADJUSTMENT';
  branch_name: string;
  vehicle_registration: string | null;
}

export interface InvestorInterimPaymentActivity {
  id: string;
  period_month: string;
  effective_at: string;
  amount: string;
}

export interface Phase5Vehicle {
  id: string;
  company_id: string;
  branch_id: string;
  branch_name: string;
  registration: string;
  model: string;
  is_active: boolean;
  is_sold: boolean;
  sale_id: string | null;
}

export interface Phase5Payment {
  id: string;
  amount: string;
  account_id: string;
  reference: string;
  effective_at: string;
}

export type Phase5Refund = Omit<Phase5Payment, 'reference'>;

export interface Phase5Purchase {
  id: string;
  vehicle_id: string;
  company_id: string;
  branch_id: string;
  purchase_cost: string;
  seller_name: string;
  seller_phone: string;
  investor_id: string | null;
  investor_fund_amount: string;
  running_capital_amount: string;
  investor_share_agreement_id?: string | null;
  investor_share_percentage_snapshot?: string | null;
  seller_paid: string;
  seller_payable: string;
  no_advance_warning: boolean;
  purchased_at: string;
  payments: Phase5Payment[];
  refunds: Phase5Refund[];
  correction_version: number;
}

export interface Phase5Expense {
  id: string;
  vehicle_id: string;
  company_id: string;
  branch_id: string;
  amount: string;
  description: string;
  investor_id: string | null;
  investor_fund_amount: string;
  running_capital_amount: string;
  paid_total: string;
  applied_refund_total: string;
  net_paid: string;
  payable: string;
  effective_at: string;
  payments: Phase5Payment[];
  refunds: Array<Phase5Refund & { applied_amount: string; excess_amount: string }>;
}

export interface Phase5Sale {
  id: string;
  company_id: string;
  vehicle_id: string;
  vehicle_registration: string;
  vehicle_model: string;
  branch_id: string;
  branch_name: string;
  sale_price: string;
  investor_funded: boolean;
  buyer_name: string;
  buyer_phone: string;
  sold_at: string;
  received_total: string;
  refunded_total: string;
  net_received: string;
  receivable: string;
  refund_payable: string;
  refund_available: string;
  correction_version: number;
  corrections: Phase5SaleCorrection[];
  receipts: Phase5Payment[];
  refunds: Phase5Refund[];
}

export interface Phase5SaleCorrection {
  id: string;
  version: number;
  previous_sale_price: string;
  sale_price: string;
  reason: string;
  effective_at: string;
  recorded_at: string;
}

export type VehicleFinancialPositionStatus =
  | 'NOT_PURCHASED'
  | 'NOT_SOLD'
  | 'PROVISIONAL_COLLECTION'
  | 'REFUND_PENDING'
  | 'LOSS_REVIEW_REQUIRED'
  | 'READY_FOR_REVIEW';

export type VehicleProfitShareStatus =
  | 'AGREEMENT_SNAPSHOT_MISSING'
  | 'NOT_APPLICABLE'
  | 'AVAILABLE'
  | 'NOT_PURCHASED';

export interface VehicleConfirmedResult {
  investor_future_adjustment_applied?: string;
  id: string;
  version: number;
  source_version: string;
  is_current: boolean;
  result_kind: 'PROFIT' | 'LOSS' | 'BREAK_EVEN';
  result_amount: string;
  investor_share_amount: string;
  investor_profit_paid: string;
  investor_profit_remaining: string;
  investor_profit_overpaid: string;
  company_share_amount: string;
  suggested_investor_loss?: string | null;
  suggested_company_loss?: string | null;
  confirmed_at: string;
  reason: string;
}

export interface VehicleFinancialPosition {
  capital_recovery?: { investor_principal: string; running_capital: string; is_current: boolean; is_complete: boolean };
  vehicle_id: string;
  company_id: string;
  branch_id: string;
  purchase_id: string | null;
  sale_id: string | null;
  investor_id: string | null;
  investor_share_agreement_id: string | null;
  investor_share_percentage_snapshot: string | null;
  profit_share_status: VehicleProfitShareStatus;
  purchase_cost: string;
  vehicle_expense_cost: string;
  total_vehicle_cost: string;
  investor_fund_cost: string;
  running_capital_cost: string;
  sale_price: string | null;
  actual_net_collection: string;
  buyer_receivable: string | null;
  buyer_refund_payable: string | null;
  calculated_result: string | null;
  suggested_loss_split?: { investor_loss: string; company_loss: string } | null;
  status: VehicleFinancialPositionStatus;
  settlement_eligible: false;
  source_version: string;
  confirmed_result: VehicleConfirmedResult | null;
  purchase_correction_version: number;
  expense_correction_versions: Array<{ expense_id: string; version: number }>;
  sale_correction_version: number;
}

export interface Phase5FundCredit {
  id: string;
  investor_id: string;
  original_investor_id: string;
  branch_id: string;
  amount: string;
  reference: string;
  effective_at: string;
  recorded_at: string;
  accounting_event_id: string | null;
  correction_version: number;
  manual_review_required: boolean;
  attribution_corrections: Array<{
    id: string;
    from_investor_id: string;
    to_investor_id: string;
    amount: string;
    effective_at: string;
    recorded_at: string;
    reason: string;
  }>;
}

export interface Phase5FundSummary {
  company_id: string;
  investor_id: string | null;
  branch_id: string | null;
  credit_total: string;
  principal_return_total: string;
  available_amount: string;
}

export interface Phase5PrincipalReturn {
  id: string;
  investor_id: string;
  branch_id: string;
  amount: string;
  reference: string;
  effective_at: string;
  recorded_at: string;
  accounting_event_id: string | null;
  allocations: Array<{ credit_id: string; amount: string }>;
}

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const money = /^-?\d+\.\d{2}$/;

function record(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function requireRecord(value: unknown, label: string): Record<string, unknown> {
  if (!record(value)) throw new Error(`Invalid ${label} response.`);
  return value;
}

function requireUuid(value: unknown, label: string): value is string {
  if (typeof value !== 'string' || !uuid.test(value)) throw new Error(`Invalid ${label} response.`);
  return true;
}

function requireMoney(value: unknown, label: string): value is string {
  if (typeof value !== 'string' || !money.test(value)) throw new Error(`Invalid ${label} response.`);
  return true;
}

function parsePage<T>(value: unknown, label: string, parseRow: (row: unknown) => T): ApiPage<T> {
  const row = requireRecord(value, label);
  if (
    typeof row.count !== 'number' ||
    !(row.next === null || typeof row.next === 'string') ||
    !(row.previous === null || typeof row.previous === 'string') ||
    !Array.isArray(row.results)
  ) throw new Error(`Invalid ${label} response.`);
  return { count: row.count, next: row.next, previous: row.previous, results: row.results.map(parseRow) };
}

function parseInvestor(value: unknown): Phase5Investor {
  const row = requireRecord(value, 'Investor');
  requireUuid(row.id, 'Investor id');
  requireUuid(row.company_id, 'Investor Company id');
  if (typeof row.name !== 'string' || typeof row.is_active !== 'boolean') throw new Error('Invalid Investor response.');
  return row as unknown as Phase5Investor;
}

function parseProfitCalendarConfiguration(value: unknown): Phase5ProfitCalendarConfiguration {
  const row = requireRecord(value, 'Investor Profit calendar configuration');
  requireUuid(row.id, 'Investor Profit calendar id');
  requireUuid(row.investor_id, 'Investor Profit calendar Investor id');
  requireUuid(row.actor_id, 'Investor Profit calendar actor id');
  if (typeof row.effective_start !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(row.effective_start) ||
      !Number.isInteger(row.duration_months) || (row.duration_months as number) < 1 ||
      !Number.isInteger(row.version) || (row.version as number) < 1 || typeof row.recorded_at !== 'string') {
    throw new Error('Invalid Investor Profit calendar configuration.');
  }
  return row as unknown as Phase5ProfitCalendarConfiguration;
}

function parseInvestorPortalBinding(value: unknown): InvestorPortalBinding | null {
  if (value === null) return null;
  const row = requireRecord(value, 'Investor portal binding');
  for (const field of ['id', 'investor_id', 'account_id']) requireUuid(row[field], `Investor binding ${field}`);
  if (typeof row.login_id !== 'string' || !row.login_id || typeof row.effective_from !== 'string' ||
      !(row.effective_until === null || typeof row.effective_until === 'string')) {
    throw new Error('Invalid Investor portal binding response.');
  }
  return row as unknown as InvestorPortalBinding;
}

function parseInvestorProfitPosition(value: unknown): InvestorProfitPosition {
  const row = requireRecord(value, 'Confirmed Investor position');
  requireUuid(row.id, 'Position id');
  requireMoney(row.amount, 'Position amount');
  for (const field of ['repaid', 'future_profit_recovered', 'future_profit_applied']) {
    if (row[field] !== undefined) requireMoney(row[field], 'Position ' + field);
  }
  if (!['PAYABLE', 'RECOVERABLE', 'BALANCED'].includes(String(row.kind)) ||
      String(row.amount).startsWith('-') || typeof row.is_current !== 'boolean' ||
      typeof row.source_version !== 'string' || !/^[0-9a-f]{64}$/.test(row.source_version) ||
      typeof row.confirmed_at !== 'string' || typeof row.reason !== 'string') {
    throw new Error('Invalid confirmed Investor position.');
  }
  return row as unknown as InvestorProfitPosition;
}

function parseInvestorProfitPeriodProjection(value: unknown): InvestorProfitPeriodProjection {
  const row = requireRecord(value, 'Investor Profit period projection');
  requireUuid(row.company_id, 'Investor Profit Company id');
  requireUuid(row.investor_id, 'Investor Profit Investor id');
  const calendar = requireRecord(row.calendar, 'Investor Profit calendar');
  const calendarStatuses = ['CONFIGURED', 'SCHEDULED', 'DEFAULT_FROM_FIRST_FUND_CREDIT', 'NOT_AVAILABLE'];
  if (!calendarStatuses.includes(calendar.status as string) ||
      !(calendar.start_date === null || (typeof calendar.start_date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(calendar.start_date))) ||
      !(calendar.duration_months === null || (Number.isInteger(calendar.duration_months) && (calendar.duration_months as number) > 0)) ||
      !Array.isArray(calendar.versions)) {
    throw new Error('Invalid Investor Profit calendar projection.');
  }
  const periodStatuses = ['CALCULATED_NOT_RECONCILED', 'SOURCE_REVIEW_REQUIRED'];
  const reconciliationStatuses = ['NOT_RECONCILED', 'RECONCILED', 'RESTATEMENT_REQUIRED', 'SOURCE_REVIEW_REQUIRED'];
  const periods = Array.isArray(row.periods) ? row.periods.map((rawPeriod) => {
    const period = requireRecord(rawPeriod, 'Investor Profit period');
    for (const field of ['period_start', 'period_end']) {
      if (typeof period[field] !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(period[field] as string)) {
        throw new Error('Invalid Investor Profit period date.');
      }
    }
    if (!Number.isInteger(period.duration_months) || (period.duration_months as number) < 1 ||
        !Number.isInteger(period.result_count) || (period.result_count as number) < 0 ||
        !periodStatuses.includes(period.status as string) || period.paid_status !== 'NOT_RECONCILED' ||
        !(period.source_version === null || (typeof period.source_version === 'string' && /^[0-9a-f]{64}$/.test(period.source_version))) ||
        !reconciliationStatuses.includes(period.reconciliation_status as string) ||
        !(period.reconciliation_id === null || (typeof period.reconciliation_id === 'string' && uuid.test(period.reconciliation_id))) ||
        !(period.reconciliation_version === null || (Number.isInteger(period.reconciliation_version) && (period.reconciliation_version as number) > 0)) ||
        !(period.last_reconciled_net_position === null || typeof period.last_reconciled_net_position === 'string') ||
        !(period.last_restatement_adjustment === null || typeof period.last_restatement_adjustment === 'string') ||
        !(period.pending_restatement_adjustment === null || typeof period.pending_restatement_adjustment === 'string') ||
        ['calculated_unpaid_profit', 'historical_overpayment'].some((field) => field in period)) {
      throw new Error('Invalid Investor Profit period status.');
    }
    for (const field of ['gross_investor_profit', 'investor_loss_share', 'deal_profit_paid', 'interim_paid', 'loss_offset_applied']) {
      requireMoney(period[field], 'Investor Profit ' + field);
    }
    if (period.last_reconciled_net_position !== null) {
      requireMoney(period.last_reconciled_net_position, 'Investor Profit last_reconciled_net_position');
    }
    if (period.last_restatement_adjustment !== null) {
      requireMoney(period.last_restatement_adjustment, 'Investor Profit last_restatement_adjustment');
    }
    if (period.pending_restatement_adjustment !== null) {
      requireMoney(period.pending_restatement_adjustment, 'Investor Profit pending_restatement_adjustment');
    }
    const futureTargets = period.future_profit_targets;
    if (futureTargets !== undefined) {
      if (!Array.isArray(futureTargets)) throw new Error('Invalid future Profit targets.');
      for (const raw of futureTargets) {
        const target = requireRecord(raw, 'Future Profit target');
        requireUuid(target.profit_position_id, 'Profit position id');
        requireUuid(target.profit_result_id, 'Profit result id');
        requireMoney(target.amount, 'Future Profit amount');
        if (typeof target.label !== 'string' || !/^[0-9a-f]{64}$/.test(String(target.source_version))) {
          throw new Error('Invalid future Profit target.');
        }
      }
    }
    return {
      ...period,
      confirmed_position: period.confirmed_position == null ? null : parseInvestorProfitPosition(period.confirmed_position),
    } as unknown as InvestorProfitPeriodProjection['periods'][number];
  }) : null;
  if (!periods || !Array.isArray(calendar.versions) ||
      !['CALENDAR_NOT_AVAILABLE', 'REVIEW_REQUIRED', 'CALCULATED_NOT_RECONCILED', 'RECONCILED'].includes(row.status as string) ||
      !Number.isInteger(row.unassigned_result_count) || (row.unassigned_result_count as number) < 0 ||
      row.settlement_status !== 'NOT_IMPLEMENTED' || typeof row.notice !== 'string') {
    throw new Error('Invalid Investor Profit period projection.');
  }
  const versions = calendar.versions.map(parseProfitCalendarConfiguration);
  return {
    company_id: row.company_id as string,
    investor_id: row.investor_id as string,
    calendar: {
      status: calendar.status as InvestorProfitPeriodProjection['calendar']['status'],
      start_date: calendar.start_date as string | null,
      duration_months: calendar.duration_months as number | null,
      versions,
    },
    status: row.status as InvestorProfitPeriodProjection['status'],
    periods,
    unassigned_result_count: row.unassigned_result_count as number,
    settlement_status: 'NOT_IMPLEMENTED',
    notice: row.notice,
  };
}

function parseInvestorProfitPeriodReconciliation(value: unknown): InvestorProfitPeriodReconciliation {
  const row = requireRecord(value, 'Investor Profit period reconciliation');
  requireUuid(row.id, 'Investor Profit reconciliation id');
  requireUuid(row.investor_id, 'Investor Profit reconciliation Investor id');
  requireUuid(row.confirmed_by_id, 'Investor Profit reconciliation actor id');
  if (row.previous_reconciliation_id !== null) {
    requireUuid(row.previous_reconciliation_id, 'Previous Investor Profit reconciliation id');
  }
  for (const field of ['period_start', 'period_end']) {
    if (typeof row[field] !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(row[field] as string)) {
      throw new Error('Invalid Investor Profit reconciliation period date.');
    }
  }
  if (!Number.isInteger(row.duration_months) || (row.duration_months as number) < 1 ||
      !Number.isInteger(row.result_count) || (row.result_count as number) < 0 ||
      !Number.isInteger(row.version) || (row.version as number) < 1 ||
      typeof row.source_version !== 'string' || !/^[0-9a-f]{64}$/.test(row.source_version) ||
      typeof row.reason !== 'string' || !row.reason.trim() || typeof row.confirmed_at !== 'string') {
    throw new Error('Invalid Investor Profit period reconciliation response.');
  }
  for (const field of [
    'gross_investor_profit', 'investor_loss_share', 'deal_profit_paid', 'interim_paid',
    'loss_offset_applied', 'net_position', 'restatement_adjustment',
  ]) requireMoney(row[field], 'Investor Profit reconciliation ' + field);
  return row as unknown as InvestorProfitPeriodReconciliation;
}

function parseVehicle(value: unknown): Phase5Vehicle {
  const row = requireRecord(value, 'Vehicle');
  requireUuid(row.id, 'Vehicle id');
  requireUuid(row.company_id, 'Vehicle Company id');
  requireUuid(row.branch_id, 'Vehicle Branch id');
  if (
    typeof row.branch_name !== 'string' || typeof row.registration !== 'string' || typeof row.model !== 'string' ||
    typeof row.is_active !== 'boolean' || typeof row.is_sold !== 'boolean' ||
    !(row.sale_id === null || (typeof row.sale_id === 'string' && uuid.test(row.sale_id)))
  ) throw new Error('Invalid Vehicle response.');
  return row as unknown as Phase5Vehicle;
}

function parsePayment(value: unknown): Phase5Payment {
  const row = requireRecord(value, 'Payment');
  requireUuid(row.id, 'Payment id');
  requireUuid(row.account_id, 'Payment account id');
  requireMoney(row.amount, 'Payment amount');
  if (typeof row.reference !== 'string' || typeof row.effective_at !== 'string') throw new Error('Invalid Payment response.');
  return row as unknown as Phase5Payment;
}

function parseRefund(value: unknown): Phase5Refund {
  const row = requireRecord(value, 'Refund');
  requireUuid(row.id, 'Refund id');
  requireUuid(row.account_id, 'Refund account id');
  requireMoney(row.amount, 'Refund amount');
  if (typeof row.effective_at !== 'string') throw new Error('Invalid Refund response.');
  return row as unknown as Phase5Refund;
}

function parseExpenseRefund(value: unknown): Phase5Refund & { applied_amount: string; excess_amount: string } {
  const refund = parseRefund(value);
  const row = requireRecord(value, 'Expense refund');
  requireMoney(row.applied_amount, 'Expense refund applied amount');
  requireMoney(row.excess_amount, 'Expense refund excess amount');
  return { ...refund, applied_amount: row.applied_amount as string, excess_amount: row.excess_amount as string };
}

function parsePurchase(value: unknown): Phase5Purchase {
  const row = requireRecord(value, 'Vehicle Purchase');
  for (const field of ['id', 'vehicle_id', 'company_id', 'branch_id']) requireUuid(row[field], `Purchase ${field}`);
  for (const field of ['purchase_cost', 'investor_fund_amount', 'running_capital_amount', 'seller_paid', 'seller_payable']) requireMoney(row[field], `Purchase ${field}`);
  if (
    typeof row.seller_name !== 'string' || typeof row.seller_phone !== 'string' ||
    !(row.investor_id === null || (typeof row.investor_id === 'string' && uuid.test(row.investor_id))) ||
    typeof row.no_advance_warning !== 'boolean' || typeof row.purchased_at !== 'string' ||
    !Array.isArray(row.payments) || !Array.isArray(row.refunds) || !Number.isInteger(row.correction_version)
  ) throw new Error('Invalid Vehicle Purchase response.');
  return { ...row, payments: row.payments.map(parsePayment), refunds: row.refunds.map(parseRefund) } as unknown as Phase5Purchase;
}

function parseExpense(value: unknown): Phase5Expense {
  const row = requireRecord(value, 'Vehicle Expense');
  for (const field of ['id', 'vehicle_id', 'company_id', 'branch_id']) requireUuid(row[field], `Expense ${field}`);
  for (const field of ['amount', 'investor_fund_amount', 'running_capital_amount', 'paid_total', 'applied_refund_total', 'net_paid', 'payable']) requireMoney(row[field], `Expense ${field}`);
  if (
    typeof row.description !== 'string' || typeof row.effective_at !== 'string' ||
    !(row.investor_id === null || (typeof row.investor_id === 'string' && uuid.test(row.investor_id))) ||
    !Array.isArray(row.payments) || !Array.isArray(row.refunds)
  ) throw new Error('Invalid Vehicle Expense response.');
  return { ...row, payments: row.payments.map(parsePayment), refunds: row.refunds.map(parseExpenseRefund) } as unknown as Phase5Expense;
}

function parseSaleCorrection(value: unknown): Phase5SaleCorrection {
  const row = requireRecord(value, 'Sale correction');
  requireUuid(row.id, 'Sale correction id');
  requireMoney(row.previous_sale_price, 'Sale correction previous price');
  requireMoney(row.sale_price, 'Sale correction price');
  if (
    !Number.isInteger(row.version) || row.version as number < 1 ||
    typeof row.reason !== 'string' || !row.reason.trim() ||
    typeof row.effective_at !== 'string' || typeof row.recorded_at !== 'string'
  ) throw new Error('Invalid Sale correction response.');
  return row as unknown as Phase5SaleCorrection;
}

function parseSale(value: unknown): Phase5Sale {
  const row = requireRecord(value, 'Vehicle Sale');
  for (const field of ['id', 'company_id', 'vehicle_id', 'branch_id']) requireUuid(row[field], `Sale ${field}`);
  for (const field of ['sale_price', 'received_total', 'refunded_total', 'net_received', 'receivable', 'refund_available']) requireMoney(row[field], `Sale ${field}`);
  const refundPayable = row.refund_payable === undefined ? row.refund_available : row.refund_payable;
  requireMoney(refundPayable, 'Sale refund_payable');
  if (
    typeof row.vehicle_registration !== 'string' || typeof row.vehicle_model !== 'string' || typeof row.branch_name !== 'string' ||
    typeof row.buyer_name !== 'string' || typeof row.buyer_phone !== 'string' || typeof row.sold_at !== 'string' ||
    typeof row.investor_funded !== 'boolean' ||
    !Array.isArray(row.receipts) || !Array.isArray(row.refunds) || !Number.isInteger(row.correction_version) ||
    !(row.corrections === undefined || Array.isArray(row.corrections))
  ) throw new Error('Invalid Vehicle Sale response.');
  return {
    ...row,
    refund_payable: refundPayable,
    corrections: (row.corrections ?? []).map(parseSaleCorrection),
    receipts: row.receipts.map(parsePayment),
    refunds: row.refunds.map(parseRefund),
  } as unknown as Phase5Sale;
}

function parseInvestorVehicleProfitPayment(value: unknown): InvestorVehicleProfitPaymentReceipt {
  const row = requireRecord(value, 'Investor Vehicle Profit payment');
  for (const field of [
    'payment_id', 'result_confirmation_id', 'investor_id', 'vehicle_id', 'sale_id',
    'branch_id', 'account_id', 'accounting_event_id', 'movement_id',
  ]) requireUuid(row[field], `Investor Vehicle Profit payment ${field}`);
  for (const field of ['amount', 'paid_total', 'remaining_share']) {
    requireMoney(row[field], `Investor Vehicle Profit payment ${field}`);
  }
  if (typeof row.effective_at !== 'string' || Number.isNaN(Date.parse(row.effective_at))) {
    throw new Error('Invalid Investor Vehicle Profit payment date.');
  }
  return row as unknown as InvestorVehicleProfitPaymentReceipt;
}

function parseInvestorProfitLossOffsetOptions(value: unknown): InvestorProfitLossOffsetOptions {
  const row = requireRecord(value, 'Investor Loss offset options');
  requireUuid(row.loss_result_id, 'Investor Loss result id');
  requireMoney(row.loss_remaining_amount, 'Investor Loss remaining amount');
  if (!Array.isArray(row.target_options)) throw new Error('Invalid Investor Loss offset options.');
  const targetOptions = row.target_options.map((value) => {
    const target = requireRecord(value, 'Investor Profit offset target');
    for (const field of ['result_id', 'vehicle_id', 'sale_branch_id']) {
      requireUuid(target[field], `Investor Profit offset target ${field}`);
    }
    requireMoney(target.investor_share_amount, 'Investor Profit share');
    requireMoney(target.remaining_amount, 'Investor Profit remaining amount');
    if (typeof target.registration !== 'string' || typeof target.model !== 'string' ||
        typeof target.sale_date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(target.sale_date)) {
      throw new Error('Invalid Investor Profit offset target.');
    }
    return target as unknown as InvestorProfitLossOffsetTarget;
  });
  return { ...row, target_options: targetOptions } as unknown as InvestorProfitLossOffsetOptions;
}

function parseInvestorProfitLossOffset(value: unknown) {
  const row = requireRecord(value, 'Investor Loss offset');
  for (const field of ['offset_id', 'loss_result_id', 'profit_result_id', 'investor_id', 'branch_id']) {
    requireUuid(row[field], `Investor Loss offset ${field}`);
  }
  for (const field of ['amount', 'loss_remaining', 'profit_remaining']) {
    requireMoney(row[field], `Investor Loss offset ${field}`);
  }
  if (typeof row.reason !== 'string' || typeof row.effective_at !== 'string' || Number.isNaN(Date.parse(row.effective_at))) {
    throw new Error('Invalid Investor Loss offset response.');
  }
  return row;
}

function parseVehicleFinancialPosition(value: unknown): VehicleFinancialPosition {
  const row = requireRecord(value, 'Vehicle financial position');
  if (typeof row.source_version !== 'string' || !/^[0-9a-f]{64}$/.test(row.source_version)) {
    throw new Error('Invalid financial position source version.');
  }
  for (const field of ['vehicle_id', 'company_id', 'branch_id']) requireUuid(row[field], `Financial position ${field}`);
  for (const field of ['purchase_id', 'sale_id']) {
    if (!(row[field] === null || (typeof row[field] === 'string' && uuid.test(row[field])))) {
      throw new Error(`Invalid financial position ${field}.`);
    }
  }
  for (const field of ['investor_id', 'investor_share_agreement_id']) {
    if (!(row[field] === null || (typeof row[field] === 'string' && uuid.test(row[field])))) {
      throw new Error(`Invalid financial position ${field}.`);
    }
  }
  if (row.investor_share_percentage_snapshot !== null &&
      (typeof row.investor_share_percentage_snapshot !== 'string' || !/^\d{1,3}\.\d{4}$/.test(row.investor_share_percentage_snapshot))) {
    throw new Error('Invalid financial position investor share snapshot.');
  }
  const profitShareStatuses: VehicleProfitShareStatus[] = [
    'AGREEMENT_SNAPSHOT_MISSING', 'NOT_APPLICABLE', 'AVAILABLE', 'NOT_PURCHASED',
  ];
  if (!profitShareStatuses.includes(row.profit_share_status as VehicleProfitShareStatus)) {
    throw new Error('Invalid financial position profit share status.');
  }
  for (const field of ['purchase_cost', 'vehicle_expense_cost', 'total_vehicle_cost', 'investor_fund_cost', 'running_capital_cost', 'actual_net_collection']) {
    requireMoney(row[field], `Financial position ${field}`);
  }
  for (const field of ['buyer_receivable', 'buyer_refund_payable']) {
    if (row.sale_id === null) {
      if (row[field] !== null) throw new Error(`Invalid Financial position ${field} response.`);
    } else {
      requireMoney(row[field], `Financial position ${field}`);
    }
  }
  for (const field of ['sale_price', 'calculated_result']) {
    if (row[field] !== null) requireMoney(row[field], `Financial position ${field}`);
  }
  if (row.suggested_loss_split != null) {
    const suggestion = requireRecord(row.suggested_loss_split, 'Suggested Loss split');
    for (const field of ['investor_loss', 'company_loss']) {
      if (typeof suggestion[field] !== 'string' || !/^\d+\.\d{2}$/.test(suggestion[field] as string)) {
        throw new Error(`Invalid suggested Loss split ${field}.`);
      }
    }
  }
  const statuses: VehicleFinancialPositionStatus[] = ['NOT_PURCHASED', 'NOT_SOLD', 'PROVISIONAL_COLLECTION', 'REFUND_PENDING', 'LOSS_REVIEW_REQUIRED', 'READY_FOR_REVIEW'];
  if (!statuses.includes(row.status as VehicleFinancialPositionStatus) || row.settlement_eligible !== false ||
      !Number.isInteger(row.purchase_correction_version) || !Number.isInteger(row.sale_correction_version) ||
      !Array.isArray(row.expense_correction_versions)) {
    throw new Error('Invalid Vehicle financial position response.');
  }
  const expenseVersions = row.expense_correction_versions.map((item) => {
    const correction = requireRecord(item, 'Expense correction version');
    requireUuid(correction.expense_id, 'Expense correction id');
    if (!Number.isInteger(correction.version) || (correction.version as number) < 0) throw new Error('Invalid Expense correction version.');
    return { expense_id: correction.expense_id as string, version: correction.version as number };
  });
  let confirmedResult: VehicleConfirmedResult | null = null;
  if (row.confirmed_result !== null) {
    const result = requireRecord(row.confirmed_result, 'Confirmed Vehicle result');
    requireUuid(result.id, 'Confirmed Vehicle result id');
    if (!Number.isInteger(result.version) || (result.version as number) < 1 ||
        typeof result.source_version !== 'string' || !/^[0-9a-f]{64}$/.test(result.source_version) ||
        typeof result.is_current !== 'boolean' ||
        !['PROFIT', 'LOSS', 'BREAK_EVEN'].includes(String(result.result_kind)) ||
        typeof result.reason !== 'string' || typeof result.confirmed_at !== 'string') {
      throw new Error('Invalid confirmed Vehicle result response.');
    }
    for (const field of ['result_amount', 'investor_share_amount', 'company_share_amount', 'investor_profit_paid', 'investor_profit_remaining', 'investor_profit_overpaid']) {
      requireMoney(result[field], `Confirmed Vehicle result ${field}`);
    }
    if (result.investor_future_adjustment_applied !== undefined) {
      requireMoney(result.investor_future_adjustment_applied, 'Investor future adjustment amount');
    }
    for (const field of ['suggested_investor_loss', 'suggested_company_loss']) {
      if (result[field] != null && (typeof result[field] !== 'string' || !/^\d+\.\d{2}$/.test(result[field] as string))) {
        throw new Error(`Invalid confirmed Vehicle result ${field}.`);
      }
    }
    confirmedResult = result as unknown as VehicleConfirmedResult;
  }
  return { ...row, confirmed_result: confirmedResult, expense_correction_versions: expenseVersions } as unknown as VehicleFinancialPosition;
}

function parseInvestorPortalSnapshot(value: unknown): InvestorPortalSnapshot {
  const row = requireRecord(value, 'Investor portal profile');
  requireUuid(row.investor_id, 'Investor id');
  requireUuid(row.binding_id, 'Investor binding id');
  if (typeof row.name !== 'string' || !row.name.trim()) throw new Error('Invalid Investor portal name.');
  const fund = requireRecord(row.fund_position, 'Investor fund position');
  if (fund.withdrawal_eligible !== false || !['PHASE8_RECONCILIATION_REQUIRED', 'MANUAL_REVIEW_REQUIRED'].includes(String(fund.status))) {
    throw new Error('Invalid Investor fund position status.');
  }
  const fundFields = ['credit_total', 'principal_return_total', 'committed_vehicle_total', 'use_adjustment_total', 'ledger_available_amount'] as const;
  const fundAmounts = Object.fromEntries(fundFields.map((field) => {
    const amount = fund[field];
    if (fund.status === 'MANUAL_REVIEW_REQUIRED') {
      if (amount !== null) throw new Error(`Investor ${field} must be unavailable during manual review.`);
      return [field, null];
    }
    requireMoney(amount, `Investor ${field}`);
    return [field, amount];
  }));
  const fundPosition = {
    ...fundAmounts,
    withdrawal_eligible: false as const,
    status: fund.status as InvestorPortalSnapshot['fund_position']['status'],
  } as InvestorPortalSnapshot['fund_position'];
  if (!Array.isArray(row.vehicles) || !Array.isArray(row.vehicle_results) || !Array.isArray(row.exit_requests)) {
    throw new Error('Invalid Investor portal collections.');
  }
  const interim = requireRecord(row.interim, 'Investor interim position');
  if (!['CONFIGURED', 'NOT_CONFIGURED'].includes(String(interim.status)) || interim.payout_status !== 'NOT_RECONCILED') {
    throw new Error('Invalid Investor interim status.');
  }
  if (interim.monthly_amount !== null) requireMoney(interim.monthly_amount, 'Investor monthly interim amount');
  const calendar = requireRecord(row.profit_calendar, 'Investor profit calendar');
  if (!['DEFAULT_FROM_FIRST_FUND_CREDIT', 'CONFIGURED', 'SCHEDULED', 'NOT_AVAILABLE'].includes(String(calendar.status)) ||
      !['DEFAULT_SIX_MONTHS', 'ACCOUNTANT_CONFIGURED', null].includes(calendar.source as string | null) ||
      !Number.isInteger(calendar.duration_months) && calendar.duration_months !== null ||
      (calendar.duration_months !== null && (calendar.duration_months as number) < 1)) {
    throw new Error('Invalid Investor profit calendar.');
  }
  if (calendar.start_date !== null && (typeof calendar.start_date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(calendar.start_date))) {
    throw new Error('Invalid Investor profit calendar start date.');
  }
  if (!['MANUAL_REVIEW_REQUIRED', 'CALENDAR_NOT_AVAILABLE', 'CALENDAR_NOT_ACTIVE', 'REVIEW_REQUIRED', 'CALCULATED_NOT_RECONCILED', 'RESTATEMENT_REQUIRED', 'RECONCILED'].includes(String(row.profit_period_status)) ||
      !Number.isInteger(row.unassigned_result_count) || (row.unassigned_result_count as number) < 0 ||
      !Array.isArray(row.profit_periods)) throw new Error('Invalid Investor profit period response.');
  const profitPeriods = row.profit_periods.map((item) => {
    const period = requireRecord(item, 'Investor profit period');
    if (typeof period.period_start !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(period.period_start) ||
        typeof period.period_end !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(period.period_end) ||
        !Number.isInteger(period.duration_months) || (period.duration_months as number) < 1 ||
        !Number.isInteger(period.result_count) || (period.result_count as number) < 0 ||
        !['CALCULATED_NOT_RECONCILED', 'SOURCE_REVIEW_REQUIRED'].includes(String(period.status)) ||
        period.paid_status !== 'NOT_RECONCILED' ||
        !['NOT_RECONCILED', 'RECONCILED', 'RESTATEMENT_REQUIRED', 'SOURCE_REVIEW_REQUIRED'].includes(String(period.reconciliation_status))) {
      throw new Error('Invalid Investor profit period.');
    }
    requireMoney(period.gross_investor_profit, 'Investor gross profit');
    requireMoney(period.investor_loss_share, 'Investor loss share');
    requireMoney(period.deal_profit_paid, 'Investor deal profit paid');
    requireMoney(period.interim_paid, 'Investor Interim paid');
    requireMoney(period.loss_offset_applied, 'Investor loss offset applied');
    let confirmedSnapshot: InvestorPortalSnapshot['profit_periods'][number]['confirmed_snapshot'] = null;
    if (period.confirmed_snapshot !== null) {
      const confirmed = requireRecord(period.confirmed_snapshot, 'Investor confirmed period snapshot');
      if (!Number.isInteger(confirmed.version) || (confirmed.version as number) < 1 ||
          typeof confirmed.confirmed_at !== 'string' || Number.isNaN(Date.parse(confirmed.confirmed_at)) ||
          typeof confirmed.notice !== 'string' || !confirmed.notice.trim()) {
        throw new Error('Invalid Investor confirmed period snapshot.');
      }
      requireMoney(confirmed.gross_investor_profit, 'Confirmed Investor gross profit');
      requireMoney(confirmed.investor_loss_share, 'Confirmed Investor loss share');
      requireMoney(confirmed.deal_profit_paid, 'Confirmed Investor deal profit paid');
      requireMoney(confirmed.interim_paid, 'Confirmed Investor Interim paid');
      requireMoney(confirmed.loss_offset_applied, 'Confirmed Investor loss offset');
      requireMoney(confirmed.net_position, 'Confirmed Investor calculation position');
      requireMoney(confirmed.restatement_adjustment, 'Confirmed Investor restatement adjustment');
      if (confirmed.pending_restatement_adjustment !== null) {
        requireMoney(confirmed.pending_restatement_adjustment, 'Pending Investor restatement adjustment');
      }
      confirmedSnapshot = {
        version: confirmed.version as number,
        confirmed_at: confirmed.confirmed_at,
        gross_investor_profit: confirmed.gross_investor_profit as string,
        investor_loss_share: confirmed.investor_loss_share as string,
        deal_profit_paid: confirmed.deal_profit_paid as string,
        interim_paid: confirmed.interim_paid as string,
        loss_offset_applied: confirmed.loss_offset_applied as string,
        net_position: confirmed.net_position as string,
        restatement_adjustment: confirmed.restatement_adjustment as string,
        pending_restatement_adjustment: confirmed.pending_restatement_adjustment as string | null,
        notice: confirmed.notice,
      };
    }
    return {
      period_start: period.period_start,
      period_end: period.period_end,
      duration_months: period.duration_months as number,
      gross_investor_profit: period.gross_investor_profit as string,
      investor_loss_share: period.investor_loss_share as string,
      deal_profit_paid: period.deal_profit_paid as string,
      interim_paid: period.interim_paid as string,
      loss_offset_applied: period.loss_offset_applied as string,
      result_count: period.result_count as number,
      status: period.status as InvestorPortalSnapshot['profit_periods'][number]['status'],
      paid_status: 'NOT_RECONCILED' as const,
      reconciliation_status: period.reconciliation_status as InvestorPortalSnapshot['profit_periods'][number]['reconciliation_status'],
      confirmed_snapshot: confirmedSnapshot,
    };
  });
  const vehicles = row.vehicles.map((item) => {
    const vehicle = requireRecord(item, 'Investor vehicle');
    requireUuid(vehicle.vehicle_id, 'Investor vehicle id');
    for (const field of ['registration', 'model', 'branch_name', 'sale_status']) if (typeof vehicle[field] !== 'string') throw new Error(`Invalid Investor vehicle ${field}.`);
    if (!['CURRENT', 'STALE_REVIEW_REQUIRED', 'NOT_CONFIRMED'].includes(String(vehicle.confirmed_result_status))) throw new Error('Invalid Investor vehicle result status.');
    let confirmedResult: InvestorPortalSnapshot['vehicles'][number]['confirmed_result'];
    if (vehicle.confirmed_result !== undefined && vehicle.confirmed_result !== null) {
      const result = requireRecord(vehicle.confirmed_result, 'Investor confirmed Vehicle result');
      if (!['PROFIT', 'LOSS', 'BREAK_EVEN'].includes(String(result.result_kind)) ||
          typeof result.confirmed_at !== 'string' || typeof result.current !== 'boolean') {
        throw new Error('Invalid Investor confirmed Vehicle result.');
      }
      requireMoney(result.investor_share_amount, 'Investor confirmed result share');
      requireMoney(result.deal_profit_paid, 'Investor confirmed result profit paid');
      requireMoney(result.loss_offset_applied, 'Investor confirmed result loss offset');
      confirmedResult = {
        result_kind: result.result_kind as 'PROFIT' | 'LOSS' | 'BREAK_EVEN',
        investor_share_amount: result.investor_share_amount as string,
        deal_profit_paid: result.deal_profit_paid as string,
        loss_offset_applied: result.loss_offset_applied as string,
        confirmed_at: result.confirmed_at as string,
        current: result.current,
      };
    }
    return {
      vehicle_id: vehicle.vehicle_id as string,
      registration: vehicle.registration as string,
      model: vehicle.model as string,
      branch_name: vehicle.branch_name as string,
      sale_status: vehicle.sale_status as string,
      confirmed_result_status: vehicle.confirmed_result_status as InvestorPortalSnapshot['vehicles'][number]['confirmed_result_status'],
      ...(confirmedResult ? { confirmed_result: confirmedResult } : {}),
    };
  });
  const exitRequests = row.exit_requests.map((item) => {
    const request = requireRecord(item, 'Investor Exit request');
    requireUuid(request.id, 'Investor Exit request id');
    if (!['REQUESTED', 'CANCELLATION_PENDING', 'CANCELLED'].includes(String(request.status)) ||
        typeof request.terms_version !== 'string' || typeof request.terms_accepted_at !== 'string' ||
        typeof request.requested_at !== 'string' || !Array.isArray(request.history)) {
      throw new Error('Invalid Investor Exit request.');
    }
    for (const field of ['initial_notice_deadline', 'notice_deadline']) {
      if (request[field] !== undefined && (typeof request[field] !== 'string' || Number.isNaN(Date.parse(request[field] as string)))) {
        throw new Error('Invalid Investor Exit notice deadline.');
      }
    }
    let extensions: NonNullable<InvestorPortalSnapshot['exit_requests'][number]['notice_extensions']> = [];
    if (request.notice_extensions !== undefined) {
      if (!Array.isArray(request.notice_extensions)) throw new Error('Invalid Investor Exit notice extensions.');
      extensions = request.notice_extensions.map((item) => {
        const extension = requireRecord(item, 'Investor Exit notice extension');
        requireUuid(extension.id, 'Investor Exit notice extension id');
        if (!Number.isInteger(extension.version) || (extension.version as number) < 1 ||
            typeof extension.reason !== 'string' ||
            !['previous_deadline', 'deadline', 'recorded_at'].every((field) => typeof extension[field] === 'string' && !Number.isNaN(Date.parse(extension[field] as string)))) {
          throw new Error('Invalid Investor Exit notice extension.');
        }
        return { id: extension.id as string, version: extension.version as number,
          previous_deadline: extension.previous_deadline as string, deadline: extension.deadline as string,
          reason: extension.reason as string, recorded_at: extension.recorded_at as string };
      });
    }
    const history = request.history.map((entry) => {
      const event = requireRecord(entry, 'Investor Exit history event');
      if (!Number.isInteger(event.version) || (event.version as number) < 1 ||
          typeof event.action !== 'string' || typeof event.new_status !== 'string' ||
          !(event.previous_status === null || typeof event.previous_status === 'string') ||
          typeof event.reason !== 'string' || typeof event.recorded_at !== 'string' || Number.isNaN(Date.parse(event.recorded_at))) {
        throw new Error('Invalid Investor Exit history event.');
      }
      return {
        version: event.version as number,
        action: event.action as string,
        previous_status: event.previous_status as string | null,
        new_status: event.new_status as string,
        reason: event.reason as string,
        recorded_at: event.recorded_at as string,
      };
    });
    return {
      id: request.id as string,
      status: request.status as InvestorPortalSnapshot['exit_requests'][number]['status'],
      terms_version: request.terms_version as string,
      terms_accepted_at: request.terms_accepted_at as string,
      requested_at: request.requested_at as string,
      initial_notice_deadline: request.initial_notice_deadline as string | undefined,
      notice_deadline: request.notice_deadline as string | undefined,
      notice_extensions: extensions,
      history,
    };
  });
  const vehicleResults = row.vehicle_results.map((item) => {
    const result = requireRecord(item, 'Investor Vehicle result');
    requireUuid(result.vehicle_id, 'Investor result Vehicle id');
    if (result.sale_id !== null) requireUuid(result.sale_id, 'Investor result Sale id');
    if (result.effective_sale_date !== null && (typeof result.effective_sale_date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(result.effective_sale_date))) throw new Error('Invalid Investor result Sale date.');
    if (!['CURRENT', 'STALE_REVIEW_REQUIRED'].includes(String(result.status)) ||
        !['PROFIT', 'LOSS', 'BREAK_EVEN'].includes(String(result.result_kind)) ||
        typeof result.confirmed_at !== 'string' || typeof result.current !== 'boolean') throw new Error('Invalid Investor result.');
    requireMoney(result.investor_share_amount, 'Investor result share');
    requireMoney(result.deal_profit_paid, 'Investor result deal profit paid');
    requireMoney(result.loss_offset_applied, 'Investor result Loss offset');
    return result as unknown as InvestorPortalSnapshot['vehicle_results'][number];
  });
  return {
    investor_id: row.investor_id as string,
    name: row.name,
    binding_id: row.binding_id as string,
    fund_position: fundPosition,
    vehicles,
    interim: {
      status: interim.status as InvestorPortalSnapshot['interim']['status'],
      monthly_amount: interim.monthly_amount as string | null,
      effective_date: interim.effective_date as string | null,
      payout_status: 'NOT_RECONCILED',
    },
    profit_calendar: {
      status: calendar.status as InvestorPortalSnapshot['profit_calendar']['status'],
      start_date: calendar.start_date as string | null,
      duration_months: calendar.duration_months as number | null,
      source: calendar.source as InvestorPortalSnapshot['profit_calendar']['source'],
    },
    profit_period_status: row.profit_period_status as InvestorPortalSnapshot['profit_period_status'],
    unassigned_result_count: row.unassigned_result_count as number,
    profit_periods: profitPeriods,
    vehicle_results: vehicleResults.map((result) => ({
      vehicle_id: result.vehicle_id,
      sale_id: result.sale_id,
      effective_sale_date: result.effective_sale_date,
      status: result.status,
      result_kind: result.result_kind,
      investor_share_amount: result.investor_share_amount,
      deal_profit_paid: result.deal_profit_paid,
      loss_offset_applied: result.loss_offset_applied,
      confirmed_at: result.confirmed_at,
      current: result.current,
    })),
    exit_requests: exitRequests,
  };
}

function parseInvestorFundActivity(value: unknown): InvestorFundActivity {
  const row = requireRecord(value, 'Investor Fund activity');
  requireUuid(row.id, 'Investor Fund activity id');
  if (typeof row.effective_at !== 'string' || Number.isNaN(Date.parse(row.effective_at)) ||
      typeof row.branch_name !== 'string' ||
      !(row.vehicle_registration === null || typeof row.vehicle_registration === 'string') ||
      !['FUND_CREDIT', 'PRINCIPAL_RETURN', 'VEHICLE_COMMITMENT', 'COMMITMENT_ADJUSTMENT'].includes(String(row.activity_type))) {
    throw new Error('Invalid Investor Fund activity response.');
  }
  requireMoney(row.amount, 'Investor Fund activity amount');
  return {
    id: row.id as string,
    effective_at: row.effective_at as string,
    amount: row.amount as string,
    activity_type: row.activity_type as InvestorFundActivity['activity_type'],
    branch_name: row.branch_name,
    vehicle_registration: row.vehicle_registration as string | null,
  };
}

function parseInvestorInterimPaymentActivity(value: unknown): InvestorInterimPaymentActivity {
  const row = requireRecord(value, 'Investor Interim payment');
  requireUuid(row.id, 'Investor Interim payment id');
  if (typeof row.period_month !== 'string' || !/^\d{4}-\d{2}-01$/.test(row.period_month) ||
      typeof row.effective_at !== 'string' || Number.isNaN(Date.parse(row.effective_at))) {
    throw new Error('Invalid Investor Interim payment response.');
  }
  requireMoney(row.amount, 'Investor Interim payment amount');
  return {
    id: row.id as string,
    period_month: row.period_month,
    effective_at: row.effective_at,
    amount: row.amount as string,
  };
}

function apiBase(companyId: string, module: 'investment' | 'vehicle-management' | 'garage' | 'labour'): string {
  requireUuid(companyId, 'Company id');
  return `tenants/${encodeURIComponent(companyId)}/${module}/`;
}

function queryPath(base: string, suffix: string, options: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options)) if (value !== undefined && value !== '') params.set(key, String(value));
  const query = params.toString();
  return `${base}${suffix}${query ? `?${query}` : ''}`;
}

function randomId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const n = Math.floor(Math.random() * 16);
    return (char === 'x' ? n : (n & 0x3) | 0x8).toString(16);
  });
}

async function bodySignature(value: string): Promise<string> {
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
  }
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) hash = Math.imul(hash ^ value.charCodeAt(index), 16777619);
  return (hash >>> 0).toString(16);
}

export async function phase5Mutation<T>(
  companyId: string,
  userId: string,
  module: 'investment' | 'vehicle-management' | 'garage' | 'labour',
  suffix: string,
  body: unknown,
  method: Extract<ApiMethod, 'POST' | 'PATCH'> = 'POST',
  validate?: (value: unknown) => T,
): Promise<T> {
  requireUuid(userId, 'User id');
  const base = apiBase(companyId, module);
  const path = `${base}${suffix.replace(/^\/+/, '')}`;
  const stableBody = JSON.stringify(body);
  const signature = await bodySignature(`${companyId}\n${userId}\n${method}\n${path}\n${stableBody}`);
  const storageKey = `virms.phase5.intent.${companyId}.${userId}.${signature}`;
  let key: string;
  try {
    const existing = sessionStorage.getItem(storageKey);
    key = existing ?? randomId();
    if (!existing) sessionStorage.setItem(storageKey, key);
  } catch {
    throw new Error('This change cannot be saved because safe retry storage is unavailable.');
  }
  const response = await requestApi<unknown>(path, { method, body, headers: { 'Idempotency-Key': key } });
  // Keep the key until the caller confirms the response is usable. The server may
  // have committed even when a malformed response cannot safely be displayed.
  let result: T;
  try {
    result = validate ? validate(response) : response as T;
  } catch {
    throw new Error('The response could not be verified. The change may have been saved; refresh the records before trying again.');
  }
  try {
    if (sessionStorage.getItem(storageKey) === key) sessionStorage.removeItem(storageKey);
  } catch {
    // Server idempotency remains authoritative if browser cleanup is unavailable.
  }
  return result;
}

export const phase5Api = {
  investorPortalSelf(companyId: string, signal?: AbortSignal) {
    return requestApi<unknown>(`${apiBase(companyId, 'investment')}portal/self/`, { signal }).then(parseInvestorPortalSnapshot);
  },
  investorPortalFundHistory(companyId: string, page: number, signal?: AbortSignal) {
    if (!Number.isInteger(page) || page < 1) throw new Error('Investor Fund history page must be a positive integer.');
    const path = queryPath(apiBase(companyId, 'investment'), 'portal/self/fund-history/', { page });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Investor Fund history', parseInvestorFundActivity));
  },
  investorPortalInterimPaymentHistory(companyId: string, page: number, signal?: AbortSignal) {
    if (!Number.isInteger(page) || page < 1) throw new Error('Investor Interim history page must be a positive integer.');
    const path = queryPath(apiBase(companyId, 'investment'), 'portal/self/interim-payment-history/', { page });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Investor Interim history', parseInvestorInterimPaymentActivity));
  },
  investorPortalBinding(companyId: string, investorId: string, signal?: AbortSignal) {
    requireUuid(investorId, 'Investor id');
    return requestApi<unknown>(`${apiBase(companyId, 'investment')}investors/${investorId}/portal-binding/`, { signal })
      .then(parseInvestorPortalBinding);
  },
  investorExitRequests(companyId: string, investorId: string, signal?: AbortSignal) {
    requireUuid(investorId, 'Investor id');
    return requestApi<unknown>(`${apiBase(companyId, 'investment')}investors/${investorId}/exit-requests/`, { signal })
      .then((value) => parsePage(value, 'Investor Exit requests', parseInvestorExitNotice));
  },
  investorExitSettlementPosition(companyId: string, investorId: string, exitRequestId: string, signal?: AbortSignal) {
    requireUuid(investorId, 'Investor id');
    requireUuid(exitRequestId, 'Investor Exit request id');
    return requestApi<unknown>(`${apiBase(companyId, 'investment')}investors/${investorId}/exit-requests/${exitRequestId}/settlement/`, { signal })
      .then(parseInvestorExitSettlementPosition);
  },
  closeInvestorExitSettlement(companyId: string, userId: string, investorId: string, exitRequestId: string, input: { expected_source_version: string; reason: string }) {
    requireUuid(investorId, 'Investor id'); requireUuid(exitRequestId, 'Investor Exit request id');
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/exit-requests/${exitRequestId}/settlement/close/`,
      { ...input, reason: input.reason.trim() }, 'POST', (value) => {
        const row = requireRecord(value, 'Investor Exit settlement closure');
        requireUuid(row.id, 'Exit settlement closure id');
        if (row.status !== 'SETTLED' || row.source_version !== input.expected_source_version) throw new Error('Invalid Investor Exit settlement closure response.');
        return row as { id: string; status: 'SETTLED'; source_version: string };
      });
  },
  recordInvestorExitPrincipalPayment(companyId: string, userId: string, investorId: string, exitRequestId: string, input: {
    branch_id: string; account_id: string; amount: string; reference: string; effective_at: string;
    expected_source_version: string; reason: string;
  }) {
    requireUuid(investorId, 'Investor id');
    requireUuid(exitRequestId, 'Investor Exit request id');
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/exit-requests/${exitRequestId}/principal-payments/`,
      { ...input, reference: input.reference.trim(), reason: input.reason.trim() }, 'POST', (value) => {
        const row = requireRecord(value, 'Investor Exit principal payment');
        requireUuid(row.id, 'Principal return id');
        requireUuid(row.investor_id, 'Investor id');
        requireUuid(row.branch_id, 'Branch id');
        requireMoney(row.amount, 'Principal return amount');
        if (row.investor_id !== investorId || row.exit_request_id !== exitRequestId ||
            typeof row.reference !== 'string' || typeof row.effective_at !== 'string' ||
            !Array.isArray(row.allocations)) throw new Error('Invalid Investor Exit principal payment response.');
        return row;
      });
  },
  recordInvestorExitLossApplication(companyId: string, userId: string, investorId: string, exitRequestId: string, input: {
    loss_result_id: string; branch_id: string; account_id?: string; source: 'AVAILABLE_FUND' | 'DIRECT_RECEIPT';
    amount: string; effective_at: string; expected_source_version: string; reason: string;
  }) {
    requireUuid(investorId, 'Investor id');
    requireUuid(exitRequestId, 'Investor Exit request id');
    requireUuid(input.loss_result_id, 'Investor Loss result id');
    if (!/^[0-9a-f]{64}$/.test(input.expected_source_version) || input.reason.trim().length < 3) {
      return Promise.reject(new Error('Exit Loss position could not be verified.'));
    }
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/exit-requests/${exitRequestId}/loss-applications/`,
      { ...input, reason: input.reason.trim() }, 'POST', (value) => {
        const row = requireRecord(value, 'Investor Exit Loss application');
        requireUuid(row.id, 'Exit Loss application id');
        requireUuid(row.exit_request_id, 'Investor Exit request id');
        requireUuid(row.loss_result_id, 'Investor Loss result id');
        requireMoney(row.amount, 'Exit Loss application amount');
        if (row.exit_request_id !== exitRequestId || row.loss_result_id !== input.loss_result_id ||
            row.source !== input.source || !Array.isArray(row.allocations)) throw new Error('Invalid Investor Exit Loss application response.');
        return row;
      });
  },
  recordInvestorExitProfitPayment(companyId: string, userId: string, investorId: string, exitRequestId: string, input: {
    position_id: string; branch_id: string; account_id: string; amount: string; effective_at: string;
    expected_source_version: string; reason: string;
  }) {
    requireUuid(investorId, 'Investor id'); requireUuid(exitRequestId, 'Investor Exit request id');
    requireUuid(input.position_id, 'Confirmed Profit position id');
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/exit-requests/${exitRequestId}/profit-payments/`,
      { ...input, reason: input.reason.trim() }, 'POST', (value) => {
        const row = requireRecord(value, 'Investor Exit Profit payment');
        requireUuid(row.id, 'Exit Profit payment id'); requireUuid(row.position_id, 'Confirmed Profit position id');
        requireMoney(row.amount, 'Exit Profit payment amount');
        if (row.exit_request_id !== exitRequestId || row.position_id !== input.position_id ||
            typeof row.accounting_event_id !== 'string' || typeof row.movement_id !== 'string')
          throw new Error('Invalid Investor Exit Profit payment response.');
        return row;
      });
  },
  extendInvestorExitNotice(companyId: string, userId: string, investorId: string, exitRequestId: string, deadline: string, reason: string) {
    requireUuid(investorId, 'Investor id');
    requireUuid(exitRequestId, 'Investor Exit request id');
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/exit-requests/${exitRequestId}/notice-extensions/`,
      { deadline, reason: reason.trim() }, 'POST', (value) => {
        const row = requireRecord(value, 'Investor Exit notice extension');
        requireUuid(row.id, 'Investor Exit notice extension id');
        if (!Number.isInteger(row.version) || (row.version as number) < 1 ||
            typeof row.previous_deadline !== 'string' || Number.isNaN(Date.parse(row.previous_deadline)) ||
            typeof row.deadline !== 'string' || Number.isNaN(Date.parse(row.deadline)) ||
            Date.parse(row.deadline) !== Date.parse(deadline) ||
            Date.parse(row.deadline) <= Date.parse(row.previous_deadline) || row.reason !== reason.trim()) {
          throw new Error('Invalid Investor Exit notice extension response.');
        }
        return row;
      });
  },
  reviewInvestorExitCancellation(companyId: string, userId: string, investorId: string, exitRequestId: string, approve: boolean, reason: string) {
    requireUuid(investorId, 'Investor id');
    requireUuid(exitRequestId, 'Investor Exit request id');
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/exit-requests/${exitRequestId}/cancellation-review/`,
      { approve, reason: reason.trim() }, 'POST', (value) => {
        const result = parseInvestorExitNotice(value);
        if (result.id !== exitRequestId || result.status !== (approve ? 'CANCELLED' : 'REQUESTED')) {
          throw new Error('Unexpected Investor Exit cancellation review response.');
        }
        return result;
      });
  },
  bindInvestorPortalAccount(companyId: string, userId: string, investorId: string, loginId: string) {
    requireUuid(investorId, 'Investor id');
    return phase5Mutation(
      companyId, userId, 'investment', `investors/${investorId}/portal-binding/`, { login_id: loginId.trim() },
      'POST', parseInvestorPortalBinding,
    );
  },
  revokeInvestorPortalBinding(companyId: string, userId: string, bindingId: string, reason: string) {
    requireUuid(bindingId, 'Investor binding id');
    return phase5Mutation(
      companyId, userId, 'investment', `portal-bindings/${bindingId}/revoke/`, { reason: reason.trim() },
      'POST', parseInvestorPortalBinding,
    );
  },
  profitCalendarConfigurations(companyId: string, investorId: string, signal?: AbortSignal) {
    requireUuid(investorId, 'Investor id');
    return requestApi<unknown>(`${apiBase(companyId, 'investment')}investors/${investorId}/profit-calendar-configurations/`, { signal })
      .then((value) => {
        if (!Array.isArray(value)) throw new Error('Invalid Investor Profit calendar list.');
        return value.map(parseProfitCalendarConfiguration);
      });
  },
  investorProfitPeriodProjection(companyId: string, investorId: string, signal?: AbortSignal) {
    requireUuid(investorId, 'Investor id');
    return requestApi<unknown>(
      `${apiBase(companyId, 'investment')}investors/${investorId}/profit-periods/`,
      { signal },
    ).then(parseInvestorProfitPeriodProjection);
  },
  configureProfitCalendar(companyId: string, userId: string, investorId: string, input: { effective_start: string; duration_months: number }) {
    requireUuid(investorId, 'Investor id');
    return phase5Mutation(
      companyId, userId, 'investment', `investors/${investorId}/profit-calendar-configurations/`, input,
      'POST', parseProfitCalendarConfiguration,
    );
  },
  requestInvestorExit(companyId: string, userId: string) {
    return phase5Mutation(companyId, userId, 'investment', 'portal/self/exit-requests/', { terms_accepted: true }, 'POST');
  },
  requestInvestorExitCancellation(companyId: string, userId: string, exitRequestId: string, reason: string) {
    requireUuid(exitRequestId, 'Investor Exit request id');
    return phase5Mutation(companyId, userId, 'investment', `portal/self/exit-requests/${exitRequestId}/cancellation/`, { reason }, 'POST');
  },
  adjustInvestorRecoverableAgainstProfit(companyId: string, userId: string, investorId: string, positionId: string,
    input: { profit_position_id: string; profit_result_id: string; amount: string;
      expected_source_version: string; expected_profit_source_version: string; reason: string }) {
    requireUuid(investorId, 'Investor id');
    requireUuid(positionId, 'Recoverable position id');
    requireUuid(input.profit_position_id, 'Profit position id');
    requireUuid(input.profit_result_id, 'Profit result id');
    requireMoney(input.amount, 'Adjustment amount');
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/profit-positions/${positionId}/future-adjustments/`, input, 'POST', (value) => {
        const row = requireRecord(value, 'Future Profit adjustment');
        requireUuid(row.id, 'Adjustment id');
        return { id: row.id as string, recoverable_position: parseInvestorProfitPosition(row.recoverable_position),
          profit_position: parseInvestorProfitPosition(row.profit_position) };
      });
  },
  receiveInvestorProfitRepayment(companyId: string, userId: string, investorId: string, positionId: string,
    input: { branch_id: string; account_id: string; amount: string; expected_source_version: string; reason: string }) {
    requireUuid(investorId, 'Investor id');
    requireUuid(positionId, 'Position id');
    requireUuid(input.branch_id, 'Branch id');
    requireUuid(input.account_id, 'Account id');
    requireMoney(input.amount, 'Repayment amount');
    return phase5Mutation(companyId, userId, 'investment',
      `investors/${investorId}/profit-positions/${positionId}/repayments/`, input, 'POST', (value) => {
        const row = requireRecord(value, 'Investor repayment');
        requireUuid(row.receipt_id, 'Receipt id');
        requireUuid(row.accounting_event_id, 'Accounting event id');
        return { receipt_id: row.receipt_id as string, accounting_event_id: row.accounting_event_id as string,
          position: parseInvestorProfitPosition(row.position) };
      });
  },
  confirmInvestorProfitPosition(companyId: string, userId: string, investorId: string,
    input: { reconciliation_id: string; expected_source_version: string; reason: string }) {
    requireUuid(investorId, 'Investor id');
    requireUuid(input.reconciliation_id, 'Reconciliation id');
    if (!/^[0-9a-f]{64}$/.test(input.expected_source_version) || input.reason.trim().length < 3) {
      throw new Error('A current source and position confirmation reason are required.');
    }
    return phase5Mutation(companyId, userId, 'investment', `investors/${investorId}/profit-positions/`,
      { ...input, reason: input.reason.trim() }, 'POST', parseInvestorProfitPosition);
  },
  reconcileInvestorProfitPeriod(
    companyId: string,
    userId: string,
    investorId: string,
    input: { period_start: string; expected_source_version: string; reason: string },
  ) {
    requireUuid(investorId, 'Investor id');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(input.period_start) ||
        !/^[0-9a-f]{64}$/.test(input.expected_source_version) ||
        input.reason.trim().length < 3) {
      throw new Error('A valid period, source version and reconciliation reason are required.');
    }
    return phase5Mutation(
      companyId,
      userId,
      'investment',
      'investors/' + investorId + '/profit-period-reconciliations/',
      { ...input, reason: input.reason.trim() },
      'POST',
      parseInvestorProfitPeriodReconciliation,
    );
  },
  vehicles(companyId: string, options: { page?: number; branchId?: string; search?: string }, signal?: AbortSignal) {
    const path = queryPath(apiBase(companyId, 'vehicle-management'), 'vehicles/', {
      page: options.page, branch_id: options.branchId, search: options.search,
    });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Vehicle list', parseVehicle));
  },
  vehicle(companyId: string, vehicleId: string, signal?: AbortSignal) {
    requireUuid(vehicleId, 'Vehicle id');
    return requestApi<unknown>(`${apiBase(companyId, 'vehicle-management')}vehicles/${vehicleId}/`, { signal }).then(parseVehicle);
  },
  vehicleFinancialPosition(companyId: string, vehicleId: string, signal?: AbortSignal) {
    requireUuid(vehicleId, 'Vehicle id');
    return requestApi<unknown>(`${apiBase(companyId, 'vehicle-management')}vehicles/${vehicleId}/financial-position/`, { signal }).then(parseVehicleFinancialPosition);
  },
  confirmVehicleResult(companyId: string, userId: string, vehicleId: string, body: { expected_source_version: string; reason: string; investor_loss_amount?: string; company_loss_amount?: string }) {
    requireUuid(vehicleId, 'Vehicle id');
    return phase5Mutation(
      companyId, userId, 'vehicle-management',
      `vehicles/${vehicleId}/financial-position/confirm/`, body, 'POST',
      (value) => {
        const row = requireRecord(value, 'Vehicle result confirmation');
        requireUuid(row.id, 'Vehicle result confirmation id');
        for (const field of ['result_amount', 'investor_share_amount', 'company_share_amount']) {
          requireMoney(row[field], `Vehicle result confirmation ${field}`);
        }
        if (typeof row.source_version !== 'string' || !/^[0-9a-f]{64}$/.test(row.source_version) ||
            !Number.isInteger(row.version) || typeof row.reason !== 'string') {
          throw new Error('Invalid Vehicle result confirmation response.');
        }
        return row;
      },
    );
  },
  recordInvestorVehicleProfitPayment(
    companyId: string,
    userId: string,
    resultConfirmationId: string,
    input: { account_id: string; amount: string; effective_at: string; description?: string },
  ) {
    requireUuid(resultConfirmationId, 'Vehicle result confirmation id');
    requireUuid(input.account_id, 'Cash/Bank account id');
    return phase5Mutation(
      companyId,
      userId,
      'investment',
      `vehicle-results/${resultConfirmationId}/profit-payments/`,
      input,
      'POST',
      parseInvestorVehicleProfitPayment,
    );
  },
  investorProfitLossOffsetOptions(companyId: string, lossResultId: string, signal?: AbortSignal) {
    requireUuid(lossResultId, 'Investor Loss result id');
    const path = `${apiBase(companyId, 'investment')}vehicle-results/${lossResultId}/profit-loss-offsets/`;
    return requestApi<unknown>(path, { signal }).then(parseInvestorProfitLossOffsetOptions);
  },
  recordInvestorProfitLossOffset(
    companyId: string,
    userId: string,
    lossResultId: string,
    input: { profit_result_id: string; amount: string; reason: string },
  ) {
    requireUuid(lossResultId, 'Investor Loss result id');
    requireUuid(input.profit_result_id, 'Investor Profit result id');
    return phase5Mutation(
      companyId,
      userId,
      'investment',
      `vehicle-results/${lossResultId}/profit-loss-offsets/`,
      input,
      'POST',
      parseInvestorProfitLossOffset,
    );
  },
  purchases(companyId: string, options: { page?: number; branchId?: string; vehicleId?: string }, signal?: AbortSignal) {
    const path = queryPath(apiBase(companyId, 'vehicle-management'), 'purchases/', {
      page: options.page, branch_id: options.branchId, vehicle_id: options.vehicleId,
    });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Purchase list', parsePurchase));
  },
  purchase(companyId: string, purchaseId: string, signal?: AbortSignal) {
    requireUuid(purchaseId, 'Purchase id');
    return requestApi<unknown>(`${apiBase(companyId, 'vehicle-management')}purchases/${purchaseId}/`, { signal }).then(parsePurchase);
  },
  expenses(companyId: string, vehicleId: string, options: { page?: number; branchId?: string } = {}, signal?: AbortSignal) {
    requireUuid(vehicleId, 'Vehicle id');
    const path = queryPath(apiBase(companyId, 'vehicle-management'), `vehicles/${vehicleId}/expenses/`, {
      page: options.page, branch_id: options.branchId,
    });
    return requestApi<unknown>(path, { signal }).then((value): ExpensePage => {
      const row = requireRecord(value, 'Vehicle Expense list');
      requireMoney(row.running_capital_total, 'Vehicle Expense Running Capital total');
      return { ...parsePage(value, 'Vehicle Expense list', parseExpense), running_capital_total: row.running_capital_total as string };
    });
  },
  expense(companyId: string, expenseId: string, signal?: AbortSignal) {
    requireUuid(expenseId, 'Expense id');
    return requestApi<unknown>(`${apiBase(companyId, 'vehicle-management')}expenses/${expenseId}/`, { signal }).then(parseExpense);
  },
  sales(companyId: string, options: { page?: number; branchId?: string }, signal?: AbortSignal) {
    const path = queryPath(apiBase(companyId, 'vehicle-management'), 'sales/', {
      page: options.page, branch_id: options.branchId,
    });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Sale list', parseSale));
  },
  sale(companyId: string, saleId: string, signal?: AbortSignal) {
    requireUuid(saleId, 'Sale id');
    return requestApi<unknown>(`${apiBase(companyId, 'vehicle-management')}sales/${saleId}/`, { signal }).then(parseSale);
  },
  investors(companyId: string, page = 1, signal?: AbortSignal) {
    const path = queryPath(apiBase(companyId, 'investment'), 'investors/', { page });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Investor list', parseInvestor));
  },
  fundCredits(companyId: string, options: { page?: number; branchId?: string; investorId?: string }, signal?: AbortSignal) {
    const path = queryPath(apiBase(companyId, 'investment'), 'fund/credits/', {
      page: options.page, branch_id: options.branchId, investor_id: options.investorId,
    });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Fund Credit list', (item) => {
      const row = requireRecord(item, 'Fund Credit');
      for (const field of ['id', 'investor_id', 'original_investor_id', 'branch_id']) requireUuid(row[field], `Fund Credit ${field}`);
      requireMoney(row.amount, 'Fund Credit amount');
      if (
        typeof row.reference !== 'string' || typeof row.effective_at !== 'string' || typeof row.recorded_at !== 'string' ||
        !Number.isInteger(row.correction_version) || typeof row.manual_review_required !== 'boolean' ||
        !Array.isArray(row.attribution_corrections)
      ) throw new Error('Invalid Fund Credit response.');
      const attributionCorrections = row.attribution_corrections.map((rawCorrection) => {
        const correction = requireRecord(rawCorrection, 'Fund Credit correction');
        for (const field of ['id', 'from_investor_id', 'to_investor_id']) requireUuid(correction[field], `Fund Credit correction ${field}`);
        requireMoney(correction.amount, 'Fund Credit correction amount');
        if (
          typeof correction.effective_at !== 'string' || typeof correction.recorded_at !== 'string' ||
          typeof correction.reason !== 'string'
        ) throw new Error('Invalid Fund Credit correction response.');
        return correction;
      });
      return { ...row, attribution_corrections: attributionCorrections } as unknown as Phase5FundCredit;
    }));
  },
  fundSummary(companyId: string, options: { branchId?: string; investorId?: string }, signal?: AbortSignal) {
    const path = queryPath(apiBase(companyId, 'investment'), 'fund/summary/', {
      branch_id: options.branchId, investor_id: options.investorId,
    });
    return requestApi<unknown>(path, { signal }).then((value) => {
      const row = requireRecord(value, 'Fund summary');
      requireUuid(row.company_id, 'Fund summary Company id');
      for (const field of ['credit_total', 'principal_return_total', 'available_amount']) requireMoney(row[field], `Fund summary ${field}`);
      return row as unknown as Phase5FundSummary;
    });
  },
  principalReturns(companyId: string, options: { page?: number; branchId?: string; investorId?: string }, signal?: AbortSignal) {
    const path = queryPath(apiBase(companyId, 'investment'), 'fund/principal-returns/', {
      page: options.page, branch_id: options.branchId, investor_id: options.investorId,
    });
    return requestApi<unknown>(path, { signal }).then((value) => parsePage(value, 'Principal return list', (item) => {
      const row = requireRecord(item, 'Principal return');
      for (const field of ['id', 'investor_id', 'branch_id']) requireUuid(row[field], `Principal return ${field}`);
      requireMoney(row.amount, 'Principal return amount');
      if (typeof row.reference !== 'string' || typeof row.effective_at !== 'string' || typeof row.recorded_at !== 'string' ||
        !(row.accounting_event_id === null || (typeof row.accounting_event_id === 'string' && uuid.test(row.accounting_event_id))) || !Array.isArray(row.allocations)) {
        throw new Error('Invalid Principal return response.');
      }
      const allocations = row.allocations.map((item) => {
        const allocation = requireRecord(item, 'Principal return allocation');
        requireUuid(allocation.credit_id, 'Principal return credit id');
        requireMoney(allocation.amount, 'Principal return allocation amount');
        return allocation as { credit_id: string; amount: string };
      });
      return { ...row, allocations } as unknown as Phase5PrincipalReturn;
    }));
  },
  paymentAccountPreference(companyId: string, signal?: AbortSignal) {
    return requestApi<{ company_id: string; account_id: string | null; account_label: string | null }>(
      `${apiBase(companyId, 'vehicle-management')}payment-account-preference/`, { signal },
    );
  },
};
