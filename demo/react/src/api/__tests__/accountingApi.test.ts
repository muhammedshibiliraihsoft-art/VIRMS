import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { accountingCorrectionPath, accountingMutation, parseAccountingEventsPage } from '../accountingApi';
import { requestApi } from '../client';

vi.mock('../client', () => ({ requestApi: vi.fn() }));

const requestMock = vi.mocked(requestApi);

const eventId = '11111111-1111-4111-8111-111111111111';

beforeEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
  requestMock.mockResolvedValue({ id: eventId });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Accounting correction resource routing', () => {
  it.each(['INCOME', 'EXPENSE'] as const)('%s uses the general event correction resource', (eventType) => {
    expect(accountingCorrectionPath(eventType, eventId, 'REVERSE_ONLY'))
      .toBe(`events/${eventId}/corrections/`);
    expect(accountingCorrectionPath(eventType, eventId, 'REVERSE_AND_REPLACE'))
      .toBe(`events/${eventId}/corrections/`);
  });

  it.each([
    ['RECEIPT', `receipts/${eventId}/corrections/`],
    ['PAYMENT', `payments/${eventId}/corrections/`],
    ['OPENING_BALANCE', `opening-balances/${eventId}/corrections/`],
  ] as const)('%s uses its typed correction resource for either outcome', (eventType, path) => {
    expect(accountingCorrectionPath(eventType, eventId, 'REVERSE_ONLY')).toBe(path);
    expect(accountingCorrectionPath(eventType, eventId, 'REVERSE_AND_REPLACE')).toBe(path);
  });

  it('uses separate Transfer reversal and replacement correction resources', () => {
    expect(accountingCorrectionPath('TRANSFER', eventId, 'REVERSE_ONLY'))
      .toBe(`transfers/${eventId}/reversals/`);
    expect(accountingCorrectionPath('TRANSFER', eventId, 'REVERSE_AND_REPLACE'))
      .toBe(`transfers/${eventId}/corrections/`);
  });

  it('rejects an invalid event identity', () => {
    expect(() => accountingCorrectionPath('RECEIPT', 'not-a-uuid', 'REVERSE_ONLY'))
      .toThrow('A valid Accounting event identity is required.');
  });

  it('accepts a Garage source receipt without routing correction to transfers', () => {
    const row = { id: eventId, company_id: eventId, branch_id: null, branch_name: null,
      event_type: 'GARAGE_RECEIPT', amount: '200.00', currency: 'INR', category_id: null,
      category_name: null, description: 'Garage customer receipt', source_reference: 'voucher-1',
      effective_at: '2026-11-17T00:00:00Z', recorded_at: '2026-11-17T00:00:00Z', actor_id: eventId,
      effect_sign: 1, reversal_of_id: null, replaces_event_id: null };
    expect(parseAccountingEventsPage({ count: 1, next: null, previous: null, results: [row] }).results[0].event_type).toBe('GARAGE_RECEIPT');
    expect(() => accountingCorrectionPath('GARAGE_RECEIPT', eventId, 'REVERSE_ONLY')).toThrow('owning workflow');
  });

  it('reads Vehicle Company Share as a source-linked non-cash result, not a generic correction', () => {
    const row = { id: eventId, company_id: eventId, branch_id: eventId, branch_name: 'Central',
      event_type: 'VEHICLE_COMPANY_SHARE', amount: '250.00', currency: 'INR', category_id: null,
      category_name: null, description: 'Verified Company Share', source_reference: 'vehicle-company-share:result-1',
      effective_at: '2026-11-17T00:00:00Z', recorded_at: '2026-11-17T00:00:00Z', actor_id: eventId,
      effect_sign: 1, reversal_of_id: null, replaces_event_id: null };
    const parsed = parseAccountingEventsPage({ count: 1, next: null, previous: null, results: [row] });

    expect(parsed.results[0].event_type).toBe('VEHICLE_COMPANY_SHARE');
    expect(() => accountingCorrectionPath('VEHICLE_COMPANY_SHARE', eventId, 'REVERSE_ONLY'))
      .toThrow('owning workflow');
  });

  it('reads Owner distributions as cash events without treating them as generic Payments', () => {
    const row = { id: eventId, company_id: eventId, branch_id: eventId, branch_name: 'Central',
      event_type: 'OWNER_DISTRIBUTION_PAYMENT', amount: '125.00', currency: 'INR', category_id: null,
      category_name: null, description: 'Partial owner distribution', source_reference: 'OWNER-DISTRIBUTION-1',
      effective_at: '2026-11-17T00:00:00Z', recorded_at: '2026-11-17T00:00:00Z', actor_id: eventId,
      effect_sign: 1, reversal_of_id: null, replaces_event_id: null };
    const parsed = parseAccountingEventsPage({ count: 1, next: null, previous: null, results: [row] });

    expect(parsed.results[0].event_type).toBe('OWNER_DISTRIBUTION_PAYMENT');
    expect(() => accountingCorrectionPath('OWNER_DISTRIBUTION_PAYMENT', eventId, 'REVERSE_ONLY'))
      .toThrow('owning workflow');
  });
});

describe('Accounting mutation idempotency', () => {
  it('reuses the pending idempotency key after an ambiguous network failure', async () => {
    requestMock.mockRejectedValueOnce(new Error('network failure'));
    const body = { amount: '125.00', source_reference: 'SRC-125' };

    await expect(accountingMutation(eventId, eventId, 'incomes/', 'POST', body)).rejects.toThrow('network failure');
    await accountingMutation(eventId, eventId, 'incomes/', 'POST', body);

    const firstHeaders = requestMock.mock.calls[0][1]?.headers as Record<string, string>;
    const retryHeaders = requestMock.mock.calls[1][1]?.headers as Record<string, string>;
    expect(firstHeaders['Idempotency-Key']).toBeTruthy();
    expect(retryHeaders['Idempotency-Key']).toBe(firstHeaders['Idempotency-Key']);
  });

  it('does not post a financial mutation when browser storage cannot preserve its retry key', async () => {
    vi.stubGlobal('sessionStorage', {
      getItem: () => null,
      setItem: () => { throw new DOMException('Storage is disabled.', 'SecurityError'); },
      removeItem: vi.fn(),
    });

    await expect(accountingMutation(eventId, eventId, 'incomes/', 'POST', { amount: '125.00' }))
      .rejects.toThrow('Accounting changes cannot be saved because browser retry storage is unavailable.');
    expect(requestMock).not.toHaveBeenCalled();
  });
});
