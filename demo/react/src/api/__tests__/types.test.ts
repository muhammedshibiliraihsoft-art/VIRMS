import { describe, expect, it } from 'vitest';
import { parseAuthMe, parseBranchPage } from '../types';

const companyId = 'c9f32d04-1a99-4f01-b583-52ed8b52b41a';
const userId = '0d6f183a-8cd8-4ed5-9a19-d51c92bbf4ae';
const branchId = 'a04177d5-df69-4bf2-a771-f72d91c87557';

describe('Phase 1 response validation', () => {
  it('preserves Company and Branch role provenance from /auth/me', () => {
    const value = parseAuthMe({
      id: userId,
      login_id: 'accountant-1',
      must_change_password: false,
      roles: ['accountant', 'investor'],
      tenant_ids: [companyId],
      companies: [{
        id: companyId,
        name: 'Example Company',
        roles: ['accountant', 'investor'],
        company_wide_roles: ['accountant'],
        branches_truncated: false,
        branches: [{ id: branchId, name: 'North', roles: ['investor'] }],
      }],
      company_context_truncated: false,
    });

    expect(value.companies[0].company_wide_roles).toEqual(['accountant']);
    expect(value.companies[0].branches[0].roles).toEqual(['investor']);
  });

  it('fails closed for malformed identity and context shapes', () => {
    expect(() => parseAuthMe({ id: 'not-a-uuid' })).toThrow('Invalid /auth/me response.');
    expect(() => parseAuthMe({
      id: userId,
      login_id: 'id',
      must_change_password: false,
      roles: [],
      tenant_ids: [],
      companies: [{ id: companyId, name: 'A', roles: [], branches: [] }],
      company_context_truncated: false,
    })).toThrow('Invalid /auth/me response.');
  });

  it('validates paginated Branch responses and their Company identity', () => {
    const page = parseBranchPage({
      count: 1,
      next: null,
      previous: null,
      results: [{ id: branchId, tenant_id: companyId, name: 'North' }],
    });
    expect(page.results[0].tenant_id).toBe(companyId);
    expect(() => parseBranchPage({ count: 1, next: null, previous: null, results: [{ ...page.results[0], tenant_id: 'bad' }] }))
      .toThrow('Invalid Branch response.');
  });
});
