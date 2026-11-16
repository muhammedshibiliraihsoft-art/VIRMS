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
  receipts: Phase5Payment[];
  refunds: Phase5Refund[];
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
    !Array.isArray(row.receipts) || !Array.isArray(row.refunds) || !Number.isInteger(row.correction_version)
  ) throw new Error('Invalid Vehicle Sale response.');
  return { ...row, refund_payable: refundPayable, receipts: row.receipts.map(parsePayment), refunds: row.refunds.map(parseRefund) } as unknown as Phase5Sale;
}

function apiBase(companyId: string, module: 'investment' | 'vehicle-management'): string {
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
  module: 'investment' | 'vehicle-management',
  suffix: string,
  body: unknown,
  method: Extract<ApiMethod, 'POST' | 'PATCH'> = 'POST',
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
  const result = await requestApi<T>(path, { method, body, headers: { 'Idempotency-Key': key } });
  try {
    if (sessionStorage.getItem(storageKey) === key) sessionStorage.removeItem(storageKey);
  } catch {
    // Server idempotency remains authoritative if browser cleanup is unavailable.
  }
  return result;
}

export const phase5Api = {
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
