import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/apiError';
import { authApi } from '../api/authApi';
import { SESSION_EXPIRED_EVENT } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import { AuthMe, CompanySummary } from '../api/types';

export type AuthStatus = 'loading' | 'anonymous' | 'authenticated' | 'password_change_required' | 'error';

export interface AuthContextValue {
  status: AuthStatus;
  user: AuthMe | null;
  currentCompany: CompanySummary | null;
  error: unknown;
  login: (loginId: string, password: string) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string, confirmPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  retryBootstrap: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const COMPANY_CONTEXT_ERROR = new Error('A single authorized Company context could not be verified.');

export function authScopeFingerprint(user: AuthMe): string {
  return JSON.stringify({
    userId: user.id,
    roles: [...user.roles].sort(),
    companyContextTruncated: user.company_context_truncated,
    companies: user.companies
      .map((company) => ({
        id: company.id,
        roles: [...company.roles].sort(),
        companyWideRoles: [...company.company_wide_roles].sort(),
        branchesTruncated: company.branches_truncated,
        branches: company.branches
          .map((branch) => ({ id: branch.id, roles: [...branch.roles].sort() }))
          .sort((left, right) => left.id.localeCompare(right.id)),
      }))
      .sort((left, right) => left.id.localeCompare(right.id)),
  });
}

export function isPlatformUser(user: AuthMe | null): boolean {
  return Boolean(user?.roles.includes('back_office'));
}

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const queryClient = useQueryClient();
  const [forcedAnonymous, setForcedAnonymous] = useState(false);
  const previousUserId = useRef<string | null>(null);
  const previousScope = useRef<string | null>(null);
  const meQuery = useQuery({
    queryKey: queryKeys.authMe,
    queryFn: ({ signal }) => authApi.me(signal),
    enabled: !forcedAnonymous,
    staleTime: 30_000,
    retry: false,
    refetchOnWindowFocus: true,
  });

  useEffect(() => {
    const handleExpired = () => {
      setForcedAnonymous(true);
      previousUserId.current = null;
      previousScope.current = null;
      void queryClient.cancelQueries();
      queryClient.clear();
    };
    window.addEventListener(SESSION_EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handleExpired);
  }, [queryClient]);

  const currentScope = meQuery.data ? authScopeFingerprint(meQuery.data) : null;
  useEffect(() => {
    if (!meQuery.data || !currentScope) return;
    if (previousScope.current && previousScope.current !== currentScope) {
      void queryClient.cancelQueries({ predicate: (query) => query.queryKey[0] !== 'auth' });
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'auth' });
    }
    previousUserId.current = meQuery.data.id;
    previousScope.current = currentScope;
  }, [currentScope, meQuery.data, queryClient]);

  useEffect(() => {
    if (!(meQuery.error instanceof ApiError) || meQuery.error.status !== 401 || !previousUserId.current) return;
    previousUserId.current = null;
    previousScope.current = null;
    setForcedAnonymous(true);
    void queryClient.cancelQueries();
    queryClient.clear();
  }, [meQuery.error, queryClient]);

  const login = async (loginId: string, password: string) => {
    await queryClient.cancelQueries();
    queryClient.clear();
    previousUserId.current = null;
    previousScope.current = null;
    setForcedAnonymous(true);
    await authApi.login(loginId, password);
    setForcedAnonymous(false);
    try {
      await queryClient.fetchQuery({
        queryKey: queryKeys.authMe,
        queryFn: ({ signal }) => authApi.me(signal),
        staleTime: 0,
        retry: false,
      });
    } catch (error) {
      queryClient.clear();
      previousUserId.current = null;
      previousScope.current = null;
      setForcedAnonymous(true);
      throw error;
    }
  };

  const changePassword = async (currentPassword: string, newPassword: string, confirmPassword: string) => {
    if (!meQuery.data?.must_change_password) {
      throw new Error('Password change is not required for this session.');
    }
    await authApi.changePassword(currentPassword, newPassword, confirmPassword);
    await queryClient.fetchQuery({
      queryKey: queryKeys.authMe,
      queryFn: ({ signal }) => authApi.me(signal),
      staleTime: 0,
      retry: false,
    });
  };

  const logout = async () => {
    try {
      await authApi.logout();
      await queryClient.cancelQueries();
      queryClient.clear();
      previousUserId.current = null;
      previousScope.current = null;
      setForcedAnonymous(true);
    } catch (error) {
      // The server outcome is unknown. Purge cached context, then let /me establish the session state.
      await queryClient.cancelQueries();
      queryClient.clear();
      previousUserId.current = null;
      previousScope.current = null;
      setForcedAnonymous(false);
      try {
        await queryClient.fetchQuery({
          queryKey: queryKeys.authMe,
          queryFn: ({ signal }) => authApi.me(signal),
          staleTime: 0,
          retry: false,
        });
      } catch (verificationError) {
        if (verificationError instanceof ApiError && verificationError.status === 401) {
          await queryClient.cancelQueries();
          queryClient.clear();
          previousUserId.current = null;
          previousScope.current = null;
          setForcedAnonymous(true);
          return;
        }
        throw error;
      }
      throw error;
    }
  };

  const retryBootstrap = async () => {
    setForcedAnonymous(false);
    await queryClient.fetchQuery({
      queryKey: queryKeys.authMe,
      queryFn: ({ signal }) => authApi.me(signal),
      staleTime: 0,
      retry: false,
    });
  };

  let status: AuthStatus;
  let user: AuthMe | null = meQuery.data ?? null;
  const companyCandidate =
    user && user.companies.length === 1 && !user.company_context_truncated
      ? user.companies[0]
      : null;
  const invalidCompanyScope = Boolean(
    user &&
    !isPlatformUser(user) &&
    (!companyCandidate || companyCandidate.roles.length === 0)
  );
  if (forcedAnonymous) {
    status = 'anonymous';
    user = null;
  } else if (meQuery.isPending) {
    status = 'loading';
  } else if (meQuery.error) {
    status = meQuery.error instanceof ApiError && meQuery.error.status === 401 ? 'anonymous' : 'error';
    user = null;
  } else if (meQuery.data?.must_change_password) {
    status = 'password_change_required';
  } else if (invalidCompanyScope) {
    status = 'error';
    user = null;
  } else {
    status = 'authenticated';
  }

  const currentCompany =
    user === null
      ? null
      : user.companies.length === 1 && !user.company_context_truncated
        ? user.companies[0]
        : null;

  const value: AuthContextValue = {
    status,
    user,
    currentCompany,
    error: invalidCompanyScope ? COMPANY_CONTEXT_ERROR : meQuery.error,
    login,
    changePassword,
    logout,
    retryBootstrap,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within AuthProvider.');
  return value;
}
