import { requestApi, ApiMethod } from './client';

export type AccountingEventType =
  | 'INCOME'
  | 'EXPENSE'
  | 'RECEIPT'
  | 'PAYMENT'
  | 'OPENING_BALANCE'
  | 'TRANSFER'
  | 'CAPITAL_INFLOW' | 'CAPITAL_OUTFLOW' | 'VEHICLE_PAYMENT' | 'VEHICLE_RECEIPT'
  | 'VEHICLE_REFUND_IN' | 'PURCHASE_REFUND_IN' | 'VEHICLE_SALE_RECEIPT' | 'VEHICLE_SALE_REFUND'
  | 'GARAGE_RECEIPT' | 'GARAGE_COST_PAYMENT' | 'GARAGE_COST_REFUND' | 'LABOUR_PAYMENT';

export interface AccountingEventRow {
  id: string;
  company_id: string;
  branch_id: string | null;
  branch_name: string | null;
  event_type: AccountingEventType;
  amount: string;
  currency: 'INR';
  category_id: string | null;
  category_name: string | null;
  description: string;
  source_reference: string;
  effective_at: string;
  recorded_at: string;
  actor_id: string;
  effect_sign: 1 | -1;
  reversal_of_id: string | null;
  replaces_event_id: string | null;
  account_id?: string;
  from_account_id?: string;
  to_account_id?: string;
}

export interface AccountingEventDetail extends AccountingEventRow {
  movements: Array<{ id: string; account_id: string; account_label: string; delta: string }>;
  applications: Array<{
    id: string;
    source_event_id: string;
    target_event_id: string;
    amount: string;
    effect_sign: 1 | -1;
    reversal_of_id: string | null;
    recorded_at: string;
    reason: string;
  }>;
  reversal_event_ids: string[];
  replacement_event_ids: string[];
  outstanding_amount?: string;
}

export interface AccountingAccount {
  id: string;
  account_type: 'CASH' | 'BANK';
  label: string;
  is_active: boolean;
  has_history?: boolean;
  current_balance?: string;
  balance_as_of?: string;
}

export interface AccountingCategory {
  id: string;
  kind: 'INCOME' | 'EXPENSE';
  label: string;
  is_active: boolean;
}

export interface AccountingBranch {
  id: string;
  tenant_id: string;
  name: string;
}

export interface AccountingPage<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AccountingResult {
  period: 'monthly' | 'h1' | 'h2' | 'annual';
  year: number;
  month: number | null;
  branch_id: string | null;
  timezone: 'Asia/Kolkata';
  starts_at: string;
  ends_before: string;
  income_amount: string;
  expense_amount: string;
  accounting_result_amount: string;
  currency: 'INR';
  scope: 'recorded_accounting_events';
}

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const eventTypes = new Set<AccountingEventType>([
  'INCOME', 'EXPENSE', 'RECEIPT', 'PAYMENT', 'OPENING_BALANCE', 'TRANSFER',
  'CAPITAL_INFLOW', 'CAPITAL_OUTFLOW', 'VEHICLE_PAYMENT', 'VEHICLE_RECEIPT',
  'VEHICLE_REFUND_IN', 'PURCHASE_REFUND_IN', 'VEHICLE_SALE_RECEIPT', 'VEHICLE_SALE_REFUND', 'GARAGE_RECEIPT', 'GARAGE_COST_PAYMENT', 'GARAGE_COST_REFUND', 'LABOUR_PAYMENT',
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function isEventRow(value: unknown): value is AccountingEventRow {
  if (!isRecord(value)) return false;
  return (
    typeof value.id === 'string' && uuidPattern.test(value.id) &&
    typeof value.company_id === 'string' && uuidPattern.test(value.company_id) &&
    (value.branch_id === null || (typeof value.branch_id === 'string' && uuidPattern.test(value.branch_id))) &&
    (value.branch_name === null || typeof value.branch_name === 'string') &&
    typeof value.event_type === 'string' && eventTypes.has(value.event_type as AccountingEventType) &&
    typeof value.amount === 'string' && /^-?\d+\.\d{2}$/.test(value.amount) &&
    value.currency === 'INR' &&
    (value.category_id === null || (typeof value.category_id === 'string' && uuidPattern.test(value.category_id))) &&
    (value.category_name === null || typeof value.category_name === 'string') &&
    typeof value.description === 'string' && typeof value.source_reference === 'string' &&
    typeof value.effective_at === 'string' && typeof value.recorded_at === 'string' &&
    typeof value.actor_id === 'string' && uuidPattern.test(value.actor_id) &&
    (value.effect_sign === 1 || value.effect_sign === -1) &&
    (value.reversal_of_id === null || (typeof value.reversal_of_id === 'string' && uuidPattern.test(value.reversal_of_id))) &&
    (value.replaces_event_id === null || (typeof value.replaces_event_id === 'string' && uuidPattern.test(value.replaces_event_id)))
  );
}

function parsePage<T>(value: unknown, parseRow: (row: unknown) => row is T): AccountingPage<T> {
  if (!isRecord(value) || typeof value.count !== 'number' || !Array.isArray(value.results) || !value.results.every(parseRow)) {
    throw new Error('Invalid Accounting page response.');
  }
  if (!(value.next === null || typeof value.next === 'string') || !(value.previous === null || typeof value.previous === 'string')) {
    throw new Error('Invalid Accounting page response.');
  }
  return value as unknown as AccountingPage<T>;
}

function companyPath(companyId: string, suffix: string): string {
  if (!uuidPattern.test(companyId)) throw new Error('A valid Company identity is required.');
  return `tenants/${encodeURIComponent(companyId)}/accounting/${suffix}`;
}

export function accountingCorrectionPath(
  eventType: AccountingEventType,
  eventId: string,
  outcome: 'REVERSE_ONLY' | 'REVERSE_AND_REPLACE',
): string {
  if (!uuidPattern.test(eventId)) throw new Error('A valid Accounting event identity is required.');
  const id = encodeURIComponent(eventId);
  if (eventType === 'INCOME' || eventType === 'EXPENSE') return `events/${id}/corrections/`;
  if (eventType === 'RECEIPT') return `receipts/${id}/corrections/`;
  if (eventType === 'PAYMENT') return `payments/${id}/corrections/`;
  if (eventType === 'OPENING_BALANCE') return `opening-balances/${id}/corrections/`;
  if (eventType === 'TRANSFER') return outcome === 'REVERSE_ONLY'
    ? `transfers/${id}/reversals/` : `transfers/${id}/corrections/`;
  throw new Error('This source event must be corrected through its owning workflow.');
}

export function parseAccountingEventsPage(value: unknown): AccountingPage<AccountingEventRow> {
  return parsePage(value, isEventRow);
}

export function parseAccountingEventDetail(value: unknown): AccountingEventDetail {
  if (!isEventRow(value) || !isRecord(value)) throw new Error('Invalid Accounting event response.');
  if (
    !Array.isArray(value.movements) ||
    !Array.isArray(value.applications) ||
    !Array.isArray(value.reversal_event_ids) ||
    !Array.isArray(value.replacement_event_ids)
  ) {
    throw new Error('Invalid Accounting event response.');
  }
  return value as unknown as AccountingEventDetail;
}

function isAccount(value: unknown): value is AccountingAccount {
  return isRecord(value) && typeof value.id === 'string' && uuidPattern.test(value.id) &&
    (value.account_type === 'CASH' || value.account_type === 'BANK') &&
    typeof value.label === 'string' && typeof value.is_active === 'boolean';
}

function isCategory(value: unknown): value is AccountingCategory {
  return isRecord(value) && typeof value.id === 'string' && uuidPattern.test(value.id) &&
    (value.kind === 'INCOME' || value.kind === 'EXPENSE') &&
    typeof value.label === 'string' && typeof value.is_active === 'boolean';
}

function isBranch(value: unknown): value is AccountingBranch {
  return isRecord(value) && typeof value.id === 'string' && uuidPattern.test(value.id) &&
    typeof value.tenant_id === 'string' && uuidPattern.test(value.tenant_id) &&
    typeof value.name === 'string';
}

export async function accountingEvents(
  companyId: string,
  options: { page?: number; eventType?: AccountingEventType; branchId?: string },
  signal?: AbortSignal,
): Promise<AccountingPage<AccountingEventRow>> {
  const params = new URLSearchParams();
  if (options.page && options.page > 1) params.set('page', String(options.page));
  if (options.eventType) params.set('event_type', options.eventType);
  if (options.branchId) params.set('branch_id', options.branchId);
  const query = params.toString();
  const value = await requestApi<unknown>(`${companyPath(companyId, 'events/')}${query ? `?${query}` : ''}`, { signal });
  return parseAccountingEventsPage(value);
}

export async function accountingEvent(
  companyId: string,
  eventId: string,
  signal?: AbortSignal,
): Promise<AccountingEventDetail> {
  const value = await requestApi<unknown>(companyPath(companyId, `events/${encodeURIComponent(eventId)}/`), { signal });
  const result = parseAccountingEventDetail(value);
  if (result.company_id !== companyId || result.id !== eventId) throw new Error('Invalid Accounting event response.');
  return result;
}

async function allPages<T>(
  companyId: string,
  suffix: string,
  parseRow: (row: unknown) => row is T,
  signal?: AbortSignal,
): Promise<T[]> {
  const results: T[] = [];
  for (let page = 1; page <= 1000; page += 1) {
    const value = await requestApi<unknown>(`${companyPath(companyId, suffix)}${page > 1 ? `?page=${page}` : ''}`, { signal });
    const response = parsePage(value, parseRow);
    results.push(...response.results);
    if (!response.next) return results;
  }
  throw new Error('Accounting page limit exceeded.');
}

export const accountingAccounts = (companyId: string, signal?: AbortSignal) =>
  allPages(companyId, 'accounts/', isAccount, signal);

export const accountingCategories = (companyId: string, signal?: AbortSignal) =>
  allPages(companyId, 'categories/', isCategory, signal);

export const accountingBranches = (companyId: string, signal?: AbortSignal) =>
  allPages(companyId, 'branches/', isBranch, signal);

export async function accountingResult(
  companyId: string,
  params: { period: AccountingResult['period']; year: number; month?: number; branchId?: string },
  signal?: AbortSignal,
): Promise<AccountingResult> {
  const query = new URLSearchParams({ period: params.period, year: String(params.year) });
  if (params.month) query.set('month', String(params.month));
  if (params.branchId) query.set('branch_id', params.branchId);
  const value = await requestApi<unknown>(`${companyPath(companyId, 'reports/accounting-result/')}?${query}`, { signal });
  if (
    !isRecord(value) || value.year !== params.year || value.period !== params.period ||
    typeof value.income_amount !== 'string' || typeof value.expense_amount !== 'string' ||
    typeof value.accounting_result_amount !== 'string' || value.timezone !== 'Asia/Kolkata' ||
    value.scope !== 'recorded_accounting_events'
  ) {
    throw new Error('Invalid Accounting result response.');
  }
  return value as unknown as AccountingResult;
}

function randomIntentId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function signatureFor(value: string): Promise<string> {
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
    return Array.from(new Uint8Array(bytes), (byte) => byte.toString(16).padStart(2, '0')).join('');
  }
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) hash = Math.imul(hash ^ value.charCodeAt(index), 16777619);
  return (hash >>> 0).toString(16);
}

export async function accountingMutation<T>(
  companyId: string,
  userId: string,
  path: string,
  method: Extract<ApiMethod, 'POST' | 'PATCH'>,
  body: unknown,
): Promise<T> {
  const stableBody = JSON.stringify(body);
  const signature = await signatureFor(`${companyId}\n${userId}\n${method}\n${path}\n${stableBody}`);
  const storageKey = `virms.accounting.intent.${companyId}.${userId}.${signature}`;
  let key: string;
  try {
    const existingKey = sessionStorage.getItem(storageKey);
    key = existingKey ?? randomIntentId();
    if (!existingKey) {
      sessionStorage.setItem(storageKey, key);
    }
  } catch {
    throw new Error('Accounting changes cannot be saved because browser retry storage is unavailable.');
  }
  const result = await requestApi<T>(companyPath(companyId, path), {
    method,
    body,
    headers: { 'Idempotency-Key': key },
  });
  try {
    if (sessionStorage.getItem(storageKey) === key) sessionStorage.removeItem(storageKey);
  } catch {
    // Storage can be unavailable; the server remains the mutation authority.
  }
  return result;
}
