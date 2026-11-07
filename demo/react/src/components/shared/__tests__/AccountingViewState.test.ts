import { describe, expect, it } from 'vitest';
import { resolveFormTargetEventId, resolveReallocationSourceEventId } from '../CompanyAccountingView';

describe('Company Accounting target selection', () => {
  it('uses the new target ID for a cash application reallocation', () => {
    expect(resolveFormTargetEventId('REALLOCATION', {
      target_event_id: '',
      new_target_event_id: 'new-income-id',
    })).toBe('new-income-id');
  });

  it('uses the ordinary target ID for a Receipt or Payment', () => {
    expect(resolveFormTargetEventId('RECEIPT', {
      target_event_id: 'income-id',
      new_target_event_id: '',
    })).toBe('income-id');
  });

  it('loads the linked cash event when reallocation starts from an Income or Expense', () => {
    expect(resolveReallocationSourceEventId('income-id', {
      source_event_id: 'receipt-id',
    })).toBe('receipt-id');
    expect(resolveReallocationSourceEventId('receipt-id', {
      source_event_id: 'receipt-id',
    })).toBeNull();
  });
});
