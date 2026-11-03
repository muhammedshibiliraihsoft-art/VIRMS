import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { authApi } from './authApi';
import { companyModuleStates } from './moduleApi';
import { queryKeys } from './queryKeys';
import { AuthMe } from './types';

export function hasCompanyBranchReadRole(user: AuthMe | null): boolean {
  const company = user?.companies.length === 1 && !user.company_context_truncated
    ? user.companies[0]
    : null;
  return Boolean(company?.roles.some((role) => ['owner', 'accountant', 'media'].includes(role)));
}

export function useCompanyBranches(page = 1) {
  const { status, user, currentCompany } = useAuth();
  const enabled = status === 'authenticated' && Boolean(currentCompany) && hasCompanyBranchReadRole(user);
  const queryKey = user && currentCompany
    ? queryKeys.branches(user.id, currentCompany.id, page)
    : ['branches', 'unavailable', page] as const;

  return useQuery({
    queryKey,
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return authApi.branches(currentCompany.id, page, signal);
    },
    enabled,
    retry: false,
  });
}

export function useCompanyModuleStates() {
  const { status, user, currentCompany } = useAuth();
  const enabled =
    status === 'authenticated' &&
    Boolean(currentCompany) &&
    hasCompanyBranchReadRole(user);
  const queryKey = user && currentCompany
    ? queryKeys.companyModuleStates(user.id, currentCompany.id)
    : ['companies', 'unavailable', 'module-state'] as const;

  return useQuery({
    queryKey,
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return companyModuleStates(currentCompany.id, signal);
    },
    enabled,
    retry: false,
    refetchOnWindowFocus: true,
  });
}
