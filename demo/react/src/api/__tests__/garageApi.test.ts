import { beforeEach, describe, expect, it, vi } from 'vitest';
import { garageApi } from '../garageApi';
import { requestApi } from '../client';

vi.mock('../client', () => ({ requestApi: vi.fn() }));
const request = vi.mocked(requestApi);
const id = '11111111-1111-4111-8111-111111111111';
const job = { id, branch_id: id, vehicle_id: id, vehicle_registration: 'KL01AB1234', vehicle_model: 'Car', branch_name: 'Central', context: 'EXTERNAL_CUSTOMER', contact_name: 'Customer', contact_phone: '', status: 'OPEN', status_version: 0, created_at: '2026-11-17T00:00:00Z' };

beforeEach(() => { sessionStorage.clear(); vi.clearAllMocks(); });

describe('Garage API', () => {
  it('validates customer cost balances and retains a payment retry key after an invalid response', async () => {
    const cost = { id, actor_id: id, version: 0, description: 'Parts', amount: '50.00', paid: '10.00', refunded: '0.00', payable: '40.00', created_at: '2026-11-17T00:00:00Z' };
    request.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [cost] });
    expect((await garageApi.customerCosts(id, id)).results[0].payable).toBe('40.00');
    const payment = { id, event_id: id, actor_id: id, amount: '20.00', effective_at: '2026-11-17T00:00:00Z', is_void: false };
    request.mockResolvedValueOnce({ ...payment, amount: 'invalid' }).mockResolvedValueOnce(payment);
    const body = { account_id: id, amount: '20.00' };
    await expect(garageApi.payCustomerCost(id, id, id, id, body)).rejects.toThrow('The change may have been saved');
    await garageApi.payCustomerCost(id, id, id, id, body);
    expect((request.mock.calls[2][1]?.headers as Record<string, string>)['Idempotency-Key']).toBe((request.mock.calls[1][1]?.headers as Record<string, string>)['Idempotency-Key']);
  });
  it('posts typed customer refunds and retains retry identity until response validation succeeds', async () => {
    const refund = { id, event_id: id, actor_id: id, amount: '30.00', applied_amount: '20.00', excess_amount: '10.00', income_event_id: id, effective_at: '2026-11-18T00:00:00Z' };
    request.mockResolvedValueOnce({ ...refund, applied_amount: 'invalid' }).mockResolvedValueOnce(refund);
    const body = { account_id: id, amount: '30.00', excess_income_category_id: id, excess_income_description: 'Workshop overpayment' };
    await expect(garageApi.refundCustomerCost(id, id, id, id, body)).rejects.toThrow('The change may have been saved');
    await garageApi.refundCustomerCost(id, id, id, id, body);
    expect(request.mock.calls[0][0]).toBe(`tenants/${id}/garage/jobs/${id}/customer-costs/${id}/refunds/`);
    expect((request.mock.calls[0][1]?.headers as Record<string, string>)['Idempotency-Key']).toBe((request.mock.calls[1][1]?.headers as Record<string, string>)['Idempotency-Key']);
    request.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [refund] });
    expect((await garageApi.customerCostRefunds(id, id, id)).results[0].excess_amount).toBe('10.00');
  });
  it('rejects malformed server responses before rendering', async () => {
    request.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [{ ...job, status: 'INVALID' }] });
    await expect(garageApi.jobs(id)).rejects.toThrow('Invalid Garage Job response');
  });

  it('reads Company-scoped jobs using the current page', async () => {
    request.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [job] });
    expect((await garageApi.jobs(id, 2)).results[0].id).toBe(id);
    expect(request).toHaveBeenCalledWith(`tenants/${id}/garage/jobs/?page=2`, { signal: undefined });
  });
  it('rejects invalid status history transitions', async () => {
    request.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [{ version: 1, from_status: 'OPEN', to_status: 'OPEN', actor_id: id, created_at: '2026-11-17T00:00:00Z' }] });
    await expect(garageApi.statusHistory(id, id)).rejects.toThrow('Invalid Garage status history response');
  });

  it('reuses the idempotency key after an uncertain Job creation', async () => {
    request.mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce(job);
    const body = { vehicle_id: id, branch_id: id, context: 'EXTERNAL_CUSTOMER', contact_name: 'Customer' };
    await expect(garageApi.createJob(id, id, body)).rejects.toThrow('network');
    await garageApi.createJob(id, id, body);
    const first = request.mock.calls[0][1]?.headers as Record<string, string>;
    const retry = request.mock.calls[1][1]?.headers as Record<string, string>;
    expect(first['Idempotency-Key']).toBeTruthy();
    expect(retry['Idempotency-Key']).toBe(first['Idempotency-Key']);
  });

  it('reuses the receipt key when a successful response has invalid shape', async () => {
    const receipt = { id, event_id: id, actor_id: id, amount: '20.00', reference: 'receipt-1', effective_at: '2026-11-17T00:00:00Z' };
    request.mockResolvedValueOnce({ ...receipt, amount: 'invalid' }).mockResolvedValueOnce(receipt);
    const body = { account_id: id, amount: '20.00', reference: 'receipt-1' };
    await expect(garageApi.receipt(id, id, id, body)).rejects.toThrow('The change may have been saved');
    await garageApi.receipt(id, id, id, body);
    const first = request.mock.calls[0][1]?.headers as Record<string, string>;
    const retry = request.mock.calls[1][1]?.headers as Record<string, string>;
    expect(retry['Idempotency-Key']).toBe(first['Idempotency-Key']);
    request.mockResolvedValueOnce(receipt);
    await garageApi.receipt(id, id, id, body);
    const nextIntent = request.mock.calls[2][1]?.headers as Record<string, string>;
    expect(nextIntent['Idempotency-Key']).not.toBe(first['Idempotency-Key']);
  });

  it('validates Labour payment identity and amount before displaying it', async () => {
    request.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [{ id, event_id: id, actor_id: id, amount: '20.00', effective_at: '2026-11-17T00:00:00Z', note: '' }] });
    expect((await garageApi.payments(id, id)).results[0].amount).toBe('20.00');
    request.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [{ id, event_id: id, actor_id: id, amount: '20.001', effective_at: '', note: '' }] });
    await expect(garageApi.payments(id, id)).rejects.toThrow('Invalid Labour payment response.');
  });
  it('retains the Labour payment retry key until response validation succeeds', async () => {
    const payment = { id, event_id: id, actor_id: id, amount: '20.00', effective_at: '2026-11-17T00:00:00Z', note: '' };
    request.mockResolvedValueOnce({ ...payment, event_id: 'bad' }).mockResolvedValueOnce(payment);
    const body = { account_id: id, amount: '20.00', effective_at: '2026-11-17T00:00:00Z', note: '' };
    await expect(garageApi.payPerson(id, id, id, body)).rejects.toThrow('The change may have been saved');
    await garageApi.payPerson(id, id, id, body);
    expect((request.mock.calls[1][1]?.headers as Record<string, string>)['Idempotency-Key']).toBe((request.mock.calls[0][1]?.headers as Record<string, string>)['Idempotency-Key']);
  });
});
