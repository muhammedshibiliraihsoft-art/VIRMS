import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthMe, CompanyModuleStatesResponse } from '../types';
import { AuthProvider } from '../../auth/AuthContext';
import { companyModuleStates } from '../moduleApi';
import { useCompanyModuleStates } from '../queries';
import { authApi } from '../authApi';

vi.mock('../authApi', () => ({
  authApi: { me: vi.fn() },
}));
vi.mock('../moduleApi', () => ({
  companyModuleStates: vi.fn(),
}));

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

const moduleResponse: CompanyModuleStatesResponse = {
  company_id: baseUser.companies[0].id,
  modules: [],
};

function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: React.PropsWithChildren) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><AuthProvider>{children}</AuthProvider></MemoryRouter>
    </QueryClientProvider>
  );
  return { queryClient, wrapper };
}

afterEach(() => vi.clearAllMocks());

describe('Company module-state query', () => {
  it('fetches the scoped contract for an authorized Company reader', async () => {
    vi.mocked(authApi.me).mockResolvedValue(baseUser);
    vi.mocked(companyModuleStates).mockResolvedValue(moduleResponse);
    const { queryClient, wrapper } = setup();

    const result = renderHook(() => useCompanyModuleStates(), { wrapper });

    await waitFor(() => expect(companyModuleStates).toHaveBeenCalledWith(
      baseUser.companies[0].id,
      expect.any(AbortSignal),
    ));
    expect(result.result.current.data).toEqual(moduleResponse);
    const query = queryClient.getQueryCache().find({
      queryKey: ['companies', baseUser.id, baseUser.companies[0].id, 'module-state'],
    });
    const runtimeOptions = query?.options as unknown as Record<string, unknown> | undefined;
    expect(query?.queryKey).toEqual([
      'companies', baseUser.id, baseUser.companies[0].id, 'module-state',
    ]);
    expect(runtimeOptions?.refetchOnWindowFocus).toBe(true);
    expect(runtimeOptions?.refetchInterval).toBeUndefined();
  });

  it('does not request Company module state for an Investor-only context', async () => {
    vi.mocked(authApi.me).mockResolvedValue({
      ...baseUser,
      roles: ['investor'],
      companies: [{
        ...baseUser.companies[0],
        roles: ['investor'],
        company_wide_roles: ['investor'],
      }],
    });
    const { wrapper } = setup();

    const result = renderHook(() => useCompanyModuleStates(), { wrapper });

    await waitFor(() => expect(authApi.me).toHaveBeenCalledTimes(1));
    expect(result.result.current.fetchStatus).toBe('idle');
    expect(companyModuleStates).not.toHaveBeenCalled();
  });

  it('does not request Company module state without an authorized Company context', async () => {
    vi.mocked(authApi.me).mockResolvedValue({
      ...baseUser,
      companies: [],
      tenant_ids: [],
      company_context_truncated: true,
    });
    const { wrapper } = setup();

    const result = renderHook(() => useCompanyModuleStates(), { wrapper });

    await waitFor(() => expect(authApi.me).toHaveBeenCalledTimes(1));
    expect(result.result.current.fetchStatus).toBe('idle');
    expect(companyModuleStates).not.toHaveBeenCalled();
  });
});
