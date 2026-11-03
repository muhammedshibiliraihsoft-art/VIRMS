import { afterEach, describe, expect, it, vi } from 'vitest';
import { requestApi } from '../client';
import { companyModuleStates } from '../moduleApi';
import {
  COMPANY_MODULE_CODES,
  CompanyModuleStatesResponse,
  parseCompanyModuleStates,
} from '../types';

vi.mock('../client', () => ({ requestApi: vi.fn() }));

const companyId = 'c9f32d04-1a99-4f01-b583-52ed8b52b41a';
const effectiveFrom = '2026-11-02T10:30:00Z';

const expectedCodes = [
  'accounting',
  'investment',
  'garage',
  'investor_portal',
  'vehicle_management',
  'vehicle_expense_management',
  'sales_receivables',
  'media_vehicle_publication',
  'public_vehicle_access',
  'labour',
  'reports_dashboard',
  'audit_corrections',
  'gst_tax_invoice',
  'owner_ai_assistant',
] as const;

function validResponse(): CompanyModuleStatesResponse {
  return {
    company_id: companyId,
    modules: expectedCodes.map((code, index) => ({
      code,
      state: index === 0 ? 'enabled' : 'unconfigured',
      version: index === 0 ? 1 : null,
      effective_from: index === 0 ? effectiveFrom : null,
    })),
  };
}

afterEach(() => vi.clearAllMocks());

describe('Company module-state API contract', () => {
  it('keeps the approved 14-code catalog and parses the complete projection', () => {
    expect(COMPANY_MODULE_CODES).toEqual(expectedCodes);
    const parsed = parseCompanyModuleStates(validResponse());

    expect(parsed.company_id).toBe(companyId);
    expect(parsed.modules).toHaveLength(14);
    expect(parsed.modules[0]).toEqual({
      code: 'accounting',
      state: 'enabled',
      version: 1,
      effective_from: effectiveFrom,
    });
    expect(parsed.modules[1]).toEqual({
      code: 'investment',
      state: 'unconfigured',
      version: null,
      effective_from: null,
    });
  });

  it('rejects unknown, missing, duplicate and reordered catalog entries', () => {
    const value = validResponse();
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: [{ ...value.modules[0], code: 'future_unknown' }, ...value.modules.slice(1)],
    })).toThrow('Invalid Company module-state response.');
    expect(() => parseCompanyModuleStates({ ...value, modules: value.modules.slice(1) }))
      .toThrow('Invalid Company module-state response.');
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: [value.modules[0], value.modules[0], ...value.modules.slice(2)],
    })).toThrow('Invalid Company module-state response.');
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: [...value.modules].reverse(),
    })).toThrow('Invalid Company module-state response.');
  });

  it('requires revision metadata exactly when configured', () => {
    const value = validResponse();
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: value.modules.map((row, index) => index === 0
        ? { ...row, version: null }
        : row),
    })).toThrow('Invalid Company module-state response.');
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: value.modules.map((row, index) => index === 1
        ? { ...row, version: 1 }
        : row),
    })).toThrow('Invalid Company module-state response.');
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: value.modules.map((row, index) => index === 1
        ? { ...row, state: 'disabled' }
        : row),
    })).toThrow('Invalid Company module-state response.');
  });

  it('rejects malformed Company identity, state and timestamps', () => {
    const value = validResponse();
    expect(() => parseCompanyModuleStates({ ...value, company_id: 'bad-id' }))
      .toThrow('Invalid Company module-state response.');
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: value.modules.map((row, index) => index === 0
        ? { ...row, state: 'active' }
        : row),
    })).toThrow('Invalid Company module-state response.');
    expect(() => parseCompanyModuleStates({
      ...value,
      modules: value.modules.map((row, index) => index === 0
        ? { ...row, effective_from: 'not-a-time' }
        : row),
    })).toThrow('Invalid Company module-state response.');
  });

  it('calls only the Company-scoped read endpoint and forwards cancellation', async () => {
    const signal = new AbortController().signal;
    vi.mocked(requestApi).mockResolvedValue(validResponse());

    await expect(companyModuleStates(companyId, signal)).resolves.toEqual(validResponse());
    expect(requestApi).toHaveBeenCalledWith(
      `tenants/${companyId}/module-state/`,
      { signal },
    );
  });

  it('rejects a valid contract returned for a different Company identity', async () => {
    vi.mocked(requestApi).mockResolvedValue({
      ...validResponse(),
      company_id: 'bcf7a6c8-ced1-4e21-8cbb-0f79a9fa20d1',
    });

    await expect(companyModuleStates(companyId)).rejects.toThrow(
      'Invalid Company module-state response.',
    );
  });
});
