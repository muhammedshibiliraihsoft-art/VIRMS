import { requestApi } from './client';
import { ApiPage, phase5Mutation } from './phase5Api';

export interface GarageJob {
  id: string; vehicle_id: string; branch_id: string;
  vehicle_registration: string; vehicle_model: string; branch_name: string;
  context: 'STOCK' | 'EXTERNAL_CUSTOMER'; contact_name: string; contact_phone: string;
  status: 'OPEN' | 'COMPLETED'; status_version: number; created_at: string;
  customer_charge?: string | null; charge_version?: number; received?: string;
  outstanding?: string | null; customer_cost_total?: string;
}
export interface GarageJobSummary {
  company_id: string;
  branch_id: string | null;
  total_jobs: number;
  open_jobs: number;
  completed_jobs: number;
  external_customer_jobs: number;
}

export interface GarageWork { id: string; description: string; actor_id: string; created_at: string }
export interface GarageStatusChange { version: number; from_status: 'OPEN' | 'COMPLETED'; to_status: 'OPEN' | 'COMPLETED'; actor_id: string; created_at: string }
export interface LabourPerson { id: string; branch_id: string; branch_name: string; name: string; phone: string; is_active: boolean; status_version: number; created_at: string; updated_at: string }
export interface LabourPayment { id: string; event_id: string; actor_id: string; amount: string; effective_at: string; note: string; is_void?: boolean }
export interface LabourPaymentCorrection { id: string; version: number; previous_amount: string; replacement_amount: string | null; reason: string; actor_id: string; created_at: string }
export interface LabourCorrectionResult { id: string; reversal_event_id: string; replacement_event_id: string | null }
export interface GarageCharge { id: string; version: number; amount: string; reason: string; actor_id: string; created_at: string }
export interface GarageCustomerCost { id: string; version: number; description: string; amount: string; paid: string; refunded: string; payable: string; actor_id: string; created_at: string }
export interface GarageCostPayment { id: string; event_id: string; actor_id: string; amount: string; effective_at: string; is_void: boolean }
export interface GarageRefundPreview { paid: string; previous_refunds: string; applied_amount: string; excess_amount: string }
export interface GarageCustomerCostRefund { id: string; event_id: string; amount: string; applied_amount: string; excess_amount: string; income_event_id: string | null; effective_at: string; actor_id: string }
export interface GarageReceipt { id: string; event_id: string; amount: string; reference: string; effective_at: string; actor_id: string; is_void?: boolean }
export interface GarageCostCorrection { id: string; version: number; amount: string; reason: string; actor_id: string; created_at: string }
export interface GarageStockCost { id: string; expense_id: string; amount: string; description: string; created_at: string }

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const money = /^\d+\.\d{2}$/;
const isObject = (value: unknown): value is Record<string, unknown> => Boolean(value) && typeof value === 'object' && !Array.isArray(value);
function requireId(value: unknown): asserts value is string {
  if (typeof value !== 'string' || !uuid.test(value)) throw new Error('Invalid record identity.');
}
function path(companyId: string, module: 'garage' | 'labour', suffix: string): string {
  requireId(companyId);
  return `tenants/${encodeURIComponent(companyId)}/${module}/${suffix}`;
}
function parseJob(value: unknown): GarageJob {
  if (!isObject(value)) throw new Error('Invalid Garage Job response.');
  for (const field of ['id', 'vehicle_id', 'branch_id']) requireId(value[field]);
  for (const field of ['vehicle_registration', 'vehicle_model', 'branch_name']) {
    if (typeof value[field] !== 'string') throw new Error('Invalid Garage Job response.');
  }
  if (!['STOCK', 'EXTERNAL_CUSTOMER'].includes(String(value.context)) || !['OPEN', 'COMPLETED'].includes(String(value.status)) ||
      typeof value.contact_name !== 'string' || typeof value.contact_phone !== 'string' || typeof value.created_at !== 'string' ||
      !Number.isSafeInteger(value.status_version) || Number(value.status_version) < 0) throw new Error('Invalid Garage Job response.');
  for (const field of ['customer_charge', 'received', 'outstanding', 'customer_cost_total']) {
    const entry = value[field];
    if (entry !== undefined && entry !== null && (typeof entry !== 'string' || !money.test(entry))) throw new Error('Invalid Garage Job amount.');
  }
  if (value.charge_version !== undefined && (!Number.isSafeInteger(value.charge_version) || Number(value.charge_version) < 0)) throw new Error('Invalid Garage charge version.');
  return value as unknown as GarageJob;
}
function parsePage<T>(value: unknown, parse: (row: unknown) => T): ApiPage<T> {
  if (!isObject(value) || !Number.isSafeInteger(value.count) || Number(value.count) < 0 || !Array.isArray(value.results) ||
      !(value.next === null || typeof value.next === 'string') || !(value.previous === null || typeof value.previous === 'string')) throw new Error('Invalid Garage page response.');
  return { count: value.count as number, next: value.next as string | null, previous: value.previous as string | null, results: value.results.map(parse) };
}
function parseWork(value: unknown): GarageWork {
  if (!isObject(value)) throw new Error('Invalid Garage work response.');
  requireId(value.id); requireId(value.actor_id);
  if (typeof value.description !== 'string' || typeof value.created_at !== 'string') throw new Error('Invalid Garage work response.');
  return value as unknown as GarageWork;
}
function parseStatusChange(value: unknown): GarageStatusChange {
  if (!isObject(value)) throw new Error('Invalid Garage status history response.');
  requireId(value.actor_id);
  if (!Number.isSafeInteger(value.version) || Number(value.version) < 1 || !['OPEN', 'COMPLETED'].includes(String(value.from_status)) || !['OPEN', 'COMPLETED'].includes(String(value.to_status)) || value.from_status === value.to_status || typeof value.created_at !== 'string') throw new Error('Invalid Garage status history response.');
  return value as unknown as GarageStatusChange;
}
function parsePerson(value: unknown): LabourPerson {
  if (!isObject(value)) throw new Error('Invalid Labour person response.');
  requireId(value.id); requireId(value.branch_id);
  if (typeof value.branch_name !== 'string' || typeof value.name !== 'string' || typeof value.phone !== 'string' || typeof value.is_active !== 'boolean' ||
      !Number.isSafeInteger(value.status_version) || Number(value.status_version) < 0 || typeof value.created_at !== 'string' || typeof value.updated_at !== 'string') throw new Error('Invalid Labour person response.');
  return value as unknown as LabourPerson;
}
function parseLabourPayment(value: unknown): LabourPayment {
  if (!isObject(value)) throw new Error('Invalid Labour payment response.');
  requireId(value.id); requireId(value.event_id); requireId(value.actor_id);
  if (typeof value.amount !== 'string' || !money.test(value.amount) || typeof value.effective_at !== 'string' || typeof value.note !== 'string') throw new Error('Invalid Labour payment response.');
  if (value.is_void !== undefined && typeof value.is_void !== 'boolean') throw new Error('Invalid Labour payment response.');
  return value as unknown as LabourPayment;
}
function parseCashCorrection(value: unknown): LabourPaymentCorrection {
  if (!isObject(value)) throw new Error('Invalid correction history.');
  requireId(value.id); requireId(value.actor_id);
  if (!Number.isSafeInteger(value.version) || Number(value.version) < 1 || typeof value.previous_amount !== 'string' || !money.test(value.previous_amount) || !(value.replacement_amount === null || (typeof value.replacement_amount === 'string' && money.test(value.replacement_amount))) || typeof value.reason !== 'string' || typeof value.created_at !== 'string') throw new Error('Invalid correction history.');
  return value as unknown as LabourPaymentCorrection;
}
function parseCashCorrectionResult(value: unknown): LabourCorrectionResult {
  if (!isObject(value)) throw new Error('Invalid correction response.');
  requireId(value.id); requireId(value.reversal_event_id);
  if (value.replacement_event_id !== null) requireId(value.replacement_event_id);
  return value as unknown as LabourCorrectionResult;
}
function parseCharge(value: unknown): GarageCharge {
  if (!isObject(value)) throw new Error('Invalid Garage charge response.');
  requireId(value.id); requireId(value.actor_id);
  if (!Number.isSafeInteger(value.version) || Number(value.version) < 1 || typeof value.amount !== 'string' || !money.test(value.amount) || typeof value.reason !== 'string' || typeof value.created_at !== 'string') throw new Error('Invalid Garage charge response.');
  return value as unknown as GarageCharge;
}
function parseCost(value: unknown): GarageCustomerCost {
  if (!isObject(value)) throw new Error('Invalid Garage cost response.');
  requireId(value.id); requireId(value.actor_id);
  if (!Number.isSafeInteger(value.version) || Number(value.version) < 0 || typeof value.amount !== 'string' || !money.test(value.amount) || typeof value.paid !== 'string' || !money.test(value.paid) || typeof value.refunded !== 'string' || !money.test(value.refunded) || typeof value.payable !== 'string' || !money.test(value.payable) || typeof value.description !== 'string' || typeof value.created_at !== 'string') throw new Error('Invalid Garage cost response.');
  return value as unknown as GarageCustomerCost;
}
function parseCostRefund(value: unknown): GarageCustomerCostRefund {
  if (!isObject(value)) throw new Error('Invalid Garage cost refund response.');
  requireId(value.id); requireId(value.event_id); requireId(value.actor_id);
  if (value.income_event_id !== null) requireId(value.income_event_id);
  for (const field of ['amount', 'applied_amount', 'excess_amount']) if (typeof value[field] !== 'string' || !money.test(value[field] as string)) throw new Error('Invalid Garage cost refund response.');
  if (typeof value.effective_at !== 'string') throw new Error('Invalid Garage cost refund response.');
  return value as unknown as GarageCustomerCostRefund;
}
function parseCostPayment(value: unknown): GarageCostPayment {
  if (!isObject(value)) throw new Error('Invalid Garage cost payment response.');
  requireId(value.id); requireId(value.event_id); requireId(value.actor_id);
  if (typeof value.amount !== 'string' || !money.test(value.amount) || typeof value.effective_at !== 'string' || typeof value.is_void !== 'boolean') throw new Error('Invalid Garage cost payment response.');
  return value as unknown as GarageCostPayment;
}
function parseReceipt(value: unknown): GarageReceipt {
  if (!isObject(value)) throw new Error('Invalid Garage receipt response.');
  requireId(value.id); requireId(value.event_id); requireId(value.actor_id);
  if (typeof value.amount !== 'string' || !money.test(value.amount) || typeof value.reference !== 'string' || typeof value.effective_at !== 'string') throw new Error('Invalid Garage receipt response.');
  if (value.is_void !== undefined && typeof value.is_void !== 'boolean') throw new Error('Invalid Garage receipt response.');
  return value as unknown as GarageReceipt;
}
function parseStockCost(value: unknown): GarageStockCost {
  if (!isObject(value)) throw new Error('Invalid Garage stock cost response.');
  requireId(value.id); requireId(value.expense_id);
  if (typeof value.amount !== 'string' || !money.test(value.amount) || typeof value.description !== 'string' || typeof value.created_at !== 'string') throw new Error('Invalid Garage stock cost response.');
  return value as unknown as GarageStockCost;
}
function parseCostCorrection(value: unknown): GarageCostCorrection {
  if (!isObject(value)) throw new Error('Invalid Garage cost correction response.');
  requireId(value.id); requireId(value.actor_id);
  if (!Number.isSafeInteger(value.version) || Number(value.version) < 1 || typeof value.amount !== 'string' || !money.test(value.amount) || typeof value.reason !== 'string' || typeof value.created_at !== 'string') throw new Error('Invalid Garage cost correction response.');
  return value as unknown as GarageCostCorrection;
}

export const garageApi = {
  async jobSummary(companyId: string, branchId?: string, signal?: AbortSignal): Promise<GarageJobSummary> {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    const value = await requestApi(path(companyId, 'garage', `jobs/dashboard-summary/${query}`), { signal });
    if (!isObject(value)) throw new Error('Invalid Garage Job summary response.');
    requireId(value.company_id);
    if (!(value.branch_id === null || (typeof value.branch_id === 'string' && uuid.test(value.branch_id)))) throw new Error('Invalid Garage Job summary Branch id.');
    for (const field of ['total_jobs', 'open_jobs', 'completed_jobs', 'external_customer_jobs']) {
      if (!Number.isSafeInteger(value[field]) || Number(value[field]) < 0) throw new Error('Invalid Garage Job summary count.');
    }
    return value as unknown as GarageJobSummary;
  },
  async jobs(companyId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageJob>> {
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/?page=${page}`), { signal }), parseJob);
  },
  async job(companyId: string, jobId: string, signal?: AbortSignal): Promise<GarageJob> {
    requireId(jobId);
    return parseJob(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/`), { signal }));
  },
  async work(companyId: string, jobId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageWork>> {
    requireId(jobId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/work/?page=${page}`), { signal }), parseWork);
  },
  async statusHistory(companyId: string, jobId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageStatusChange>> {
    requireId(jobId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/status-history/?page=${page}`), { signal }), parseStatusChange);
  },
  async stockCosts(companyId: string, jobId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageStockCost>> {
    requireId(jobId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/stock-costs/?page=${page}`), { signal }), parseStockCost);
  },
  async createStockCost(companyId: string, userId: string, jobId: string, body: { amount: string; description: string; investor_id: string | null }): Promise<GarageStockCost> {
    requireId(jobId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/stock-costs/create/`, body, 'POST', parseStockCost);
  },
  async linkStockCost(companyId: string, userId: string, jobId: string, expenseId: string): Promise<GarageStockCost> {
    requireId(jobId); requireId(expenseId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/stock-costs/`, { expense_id: expenseId }, 'POST', parseStockCost);
  },
  async people(companyId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<LabourPerson>> {
    return parsePage(await requestApi(path(companyId, 'labour', `people/?page=${page}`), { signal }), parsePerson);
  },
  async createJob(companyId: string, userId: string, body: unknown): Promise<GarageJob> {
    return phase5Mutation(companyId, userId, 'garage', 'jobs/', body, 'POST', parseJob);
  },
  async setStatus(companyId: string, userId: string, jobId: string, status: GarageJob['status'], expectedVersion: number): Promise<GarageJob> {
    requireId(jobId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/status/`, { status, expected_version: expectedVersion }, 'POST', parseJob);
  },
  async addWork(companyId: string, userId: string, jobId: string, description: string): Promise<GarageWork> {
    requireId(jobId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/work/`, { description }, 'POST', parseWork);
  },
  async createPerson(companyId: string, userId: string, body: unknown): Promise<LabourPerson> {
    return phase5Mutation(companyId, userId, 'labour', 'people/', body, 'POST', parsePerson);
  },
  async updatePerson(companyId: string, userId: string, personId: string, body: { name: string; phone: string; expected_updated_at: string }): Promise<LabourPerson> {
    requireId(personId);
    return phase5Mutation(companyId, userId, 'labour', `people/${encodeURIComponent(personId)}/`, body, 'PATCH', parsePerson);
  },
  async setPersonStatus(companyId: string, userId: string, personId: string, isActive: boolean, expectedVersion: number): Promise<LabourPerson> {
    requireId(personId);
    return phase5Mutation(companyId, userId, 'labour', `people/${encodeURIComponent(personId)}/status/`, { is_active: isActive, expected_version: expectedVersion }, 'POST', parsePerson);
  },
  async payments(companyId: string, personId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<LabourPayment>> {
    requireId(personId);
    return parsePage(await requestApi(path(companyId, 'labour', `people/${encodeURIComponent(personId)}/payments/?page=${page}`), { signal }), parseLabourPayment);
  },
  async payPerson(companyId: string, userId: string, personId: string, body: { account_id: string; amount: string; effective_at: string; note: string }): Promise<LabourPayment> {
    requireId(personId);
    return phase5Mutation(companyId, userId, 'labour', `people/${encodeURIComponent(personId)}/payments/`, body, 'POST', parseLabourPayment);
  },
  async labourCorrectionHistory(companyId: string, personId: string, paymentId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<LabourPaymentCorrection>> {
    requireId(personId); requireId(paymentId);
    return parsePage(await requestApi(path(companyId, 'labour', `people/${encodeURIComponent(personId)}/payments/${encodeURIComponent(paymentId)}/corrections/?page=${page}`), { signal }), parseCashCorrection);
  },
  async correctLabourPayment(companyId: string, userId: string, personId: string, paymentId: string, body: { expected_event_id: string; outcome: 'REVERSE_ONLY' | 'REVERSE_AND_REPLACE'; reason: string; replacement?: { account_id: string; amount: string; effective_at: string } }): Promise<LabourCorrectionResult> {
    requireId(personId); requireId(paymentId); requireId(body.expected_event_id);
    return phase5Mutation(companyId, userId, 'labour', `people/${encodeURIComponent(personId)}/payments/${encodeURIComponent(paymentId)}/corrections/`, body, 'POST', parseCashCorrectionResult);
  },
  async charge(companyId: string, userId: string, jobId: string, body: { amount: string; expected_version: number; reason: string }): Promise<GarageCharge> {
    requireId(jobId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/charges/`, body, 'POST', parseCharge);
  },
  async customerCost(companyId: string, userId: string, jobId: string, body: { description: string; amount: string }): Promise<GarageCustomerCost> {
    requireId(jobId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/`, body, 'POST', parseCost);
  },
  async customerCosts(companyId: string, jobId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageCustomerCost>> {
    requireId(jobId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/?page=${page}`), { signal }), parseCost);
  },
  async customerCostPayments(companyId: string, jobId: string, costId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageCostPayment>> {
    requireId(jobId); requireId(costId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/payments/?page=${page}`), { signal }), parseCostPayment);
  },
  async customerCostRefunds(companyId: string, jobId: string, costId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageCustomerCostRefund>> {
    requireId(jobId); requireId(costId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/refunds/?page=${page}`), { signal }), parseCostRefund);
  },
  async customerCostRefundPreview(companyId: string, jobId: string, costId: string, amount: string, signal?: AbortSignal): Promise<GarageRefundPreview> {
    requireId(jobId); requireId(costId);
    const query = new URLSearchParams({ amount });
    const result = await requestApi<unknown>(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/refund-preview/?${query}`), { signal });
    if (!isObject(result) || ['paid', 'previous_refunds', 'applied_amount', 'excess_amount'].some(key => typeof result[key] !== 'string' || !money.test(result[key] as string))) throw new Error('Invalid refund preview.');
    return result as unknown as GarageRefundPreview;
  },
  async payCustomerCost(companyId: string, userId: string, jobId: string, costId: string, body: { account_id: string; amount: string; effective_at?: string }): Promise<GarageCostPayment> {
    requireId(jobId); requireId(costId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/payments/`, body, 'POST', parseCostPayment);
  },
  async refundCustomerCost(companyId: string, userId: string, jobId: string, costId: string, body: { account_id: string; amount: string; effective_at?: string; excess_income_category_id?: string; excess_income_description?: string }): Promise<GarageCustomerCostRefund> {
    requireId(jobId); requireId(costId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/refunds/`, body, 'POST', parseCostRefund);
  },
  async customerCostPaymentHistory(companyId: string, jobId: string, costId: string, paymentId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<LabourPaymentCorrection>> {
    requireId(jobId); requireId(costId); requireId(paymentId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/payments/${encodeURIComponent(paymentId)}/corrections/?page=${page}`), { signal }), parseCashCorrection);
  },
  async correctCustomerCostPayment(companyId: string, userId: string, jobId: string, costId: string, paymentId: string, body: { expected_event_id: string; outcome: 'REVERSE_ONLY' | 'REVERSE_AND_REPLACE'; reason: string; replacement?: { account_id: string; amount: string; effective_at: string } }): Promise<LabourCorrectionResult> {
    requireId(jobId); requireId(costId); requireId(paymentId); requireId(body.expected_event_id);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/payments/${encodeURIComponent(paymentId)}/corrections/`, body, 'POST', parseCashCorrectionResult);
  },
  async customerCostHistory(companyId: string, jobId: string, costId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageCostCorrection>> {
    requireId(jobId); requireId(costId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/corrections/?page=${page}`), { signal }), parseCostCorrection);
  },
  async charges(companyId: string, jobId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageCharge>> {
    requireId(jobId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/charges/?page=${page}`), { signal }), parseCharge);
  },
  async receipts(companyId: string, jobId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<GarageReceipt>> {
    requireId(jobId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/receipts/?page=${page}`), { signal }), parseReceipt);
  },
  async receiptCorrectionHistory(companyId: string, jobId: string, receiptId: string, page = 1, signal?: AbortSignal): Promise<ApiPage<LabourPaymentCorrection>> {
    requireId(jobId); requireId(receiptId);
    return parsePage(await requestApi(path(companyId, 'garage', `jobs/${encodeURIComponent(jobId)}/receipts/${encodeURIComponent(receiptId)}/corrections/?page=${page}`), { signal }), parseCashCorrection);
  },
  async correctReceipt(companyId: string, userId: string, jobId: string, receiptId: string, body: { expected_event_id: string; outcome: 'REVERSE_ONLY' | 'REVERSE_AND_REPLACE'; reason: string; replacement?: { account_id: string; amount: string; effective_at: string } }): Promise<LabourCorrectionResult> {
    requireId(jobId); requireId(receiptId); requireId(body.expected_event_id);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/receipts/${encodeURIComponent(receiptId)}/corrections/`, body, 'POST', parseCashCorrectionResult);
  },
  async correctCustomerCost(companyId: string, userId: string, jobId: string, costId: string, body: { amount: string; expected_version: number; reason: string }): Promise<GarageCustomerCost> {
    requireId(jobId); requireId(costId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/customer-costs/${encodeURIComponent(costId)}/corrections/`, body, 'POST', parseCost);
  },
  async receipt(companyId: string, userId: string, jobId: string, body: { account_id: string; amount: string; reference: string; effective_at?: string }): Promise<GarageReceipt> {
    requireId(jobId);
    return phase5Mutation(companyId, userId, 'garage', `jobs/${encodeURIComponent(jobId)}/receipts/`, body, 'POST', parseReceipt);
  },
};
