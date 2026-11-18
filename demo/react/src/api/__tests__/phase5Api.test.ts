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
  it('requires a valid server-calculated Running Capital total on expense lists', async () => {
    requestMock.mockResolvedValueOnce({ count: 21, next: '?page=2', previous: null, results: [], running_capital_total: '2150.00' });
    expect((await phase5Api.expenses(ids.company, ids.vehicle, { page: 1 })).running_capital_total).toBe('2150.00');
    requestMock.mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] });
    await expect(phase5Api.expenses(ids.company, ids.vehicle)).rejects.toThrow('Invalid Vehicle Expense Running Capital total response.');
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
