import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthMe, BranchPage } from '../types';
import { AuthProvider } from '../../auth/AuthContext';
import { useCompanyBranches } from '../queries';

vi.mock('../authApi', () => ({
  authApi: {
    me: vi.fn(),
    branches: vi.fn(),
  },
}));

import { authApi } from '../authApi';

const baseUser: AuthMe = {
  id: '0d6f183a-8cd8-4ed5-9a19-d51c92bbf4ae',
  login_id: 'member-1',
  must_change_password: false,
  roles: ['accountant'],
  tenant_ids: ['c9f32d04-1a99-4f01-b583-52ed8b52b41a'],
  companies: [{
    id: 'c9f32d04-1a99-4f01-b583-52ed8b52b41a',
    name: 'Company A',
    roles: ['accountant'],
    company_wide_roles: ['accountant'],
    branches_truncated: true,
    branches: [],
  }],
  company_context_truncated: false,
};

function wrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: React.PropsWithChildren) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><AuthProvider>{children}</AuthProvider></MemoryRouter>
    </QueryClientProvider>
  );
}

afterEach(() => vi.clearAllMocks());

describe('authorized Branch context query', () => {
  it('fetches only the authenticated user Company and keys it by user, Company and page', async () => {
    vi.mocked(authApi.me).mockResolvedValue(baseUser);
    vi.mocked(authApi.branches).mockResolvedValue({
      count: 0, next: null, previous: null, results: [],
    } satisfies BranchPage);

    const result = renderHook(() => useCompanyBranches(2), { wrapper: wrapper() });

    await waitFor(() => expect(authApi.branches).toHaveBeenCalledWith(
      baseUser.companies[0].id, 2, expect.any(AbortSignal)
    ));
    expect(result.result.current.data?.count).toBe(0);
    expect(result.result.current.dataUpdatedAt).toBeGreaterThan(0);
  });

  it('does not request Branches for an Investor-only context', async () => {
    vi.mocked(authApi.me).mockResolvedValue({
      ...baseUser,
      roles: ['investor'],
      companies: [{ ...baseUser.companies[0], roles: ['investor'], company_wide_roles: ['investor'] }],
    });

    const result = renderHook(() => useCompanyBranches(), { wrapper: wrapper() });

    await waitFor(() => expect(authApi.me).toHaveBeenCalledTimes(1));
    expect(result.result.current.fetchStatus).toBe('idle');
    expect(authApi.branches).not.toHaveBeenCalled();
  });

  it('allows Branch reads for Media when the backend role contract exposes read scope', async () => {
    const mediaUser = {
      ...baseUser,
      roles: ['media'],
      companies: [{ ...baseUser.companies[0], roles: ['media'], company_wide_roles: ['media'] }],
    };
    vi.mocked(authApi.me).mockResolvedValue(mediaUser);
    vi.mocked(authApi.branches).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [{ id: 'd2f7c9a0-cbed-4ca8-8859-2b32a4f6820a', tenant_id: mediaUser.companies[0].id, name: 'Media Branch' }],
    });

    renderHook(() => useCompanyBranches(), { wrapper: wrapper() });

    await waitFor(() => expect(authApi.branches).toHaveBeenCalledWith(
      mediaUser.companies[0].id, 1, expect.any(AbortSignal)
    ));
  });
});
