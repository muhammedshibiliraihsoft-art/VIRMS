import { useQuery } from '@tanstack/react-query';
import {
  accountingAccounts,
  accountingBranches,
  accountingCategories,
  accountingEvent,
  accountingEvents,
  accountingMonthlyTrend,
  accountingResult,
  AccountingEventType,
} from './accountingApi';
import { useAuth } from '../auth/AuthContext';
import { queryKeys } from './queryKeys';
import { hasCompanyBranchReadRole } from './queries';

function useAccountingContext() {
  const { status, user, currentCompany } = useAuth();
  return {
    user,
    currentCompany,
    enabled: status === 'authenticated' && Boolean(currentCompany) && hasCompanyBranchReadRole(user),
  };
}

export function useAccountingBranches() {
  const { user, currentCompany, enabled } = useAccountingContext();
  return useQuery({
    queryKey: user && currentCompany
      ? queryKeys.accountingBranches(user.id, currentCompany.id)
      : ['companies', 'unavailable', 'accounting', 'branches'] as const,
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return accountingBranches(currentCompany.id, signal);
    },
    enabled,
    retry: false,
  });
}

export function useAccountingAccounts() {
  const { user, currentCompany, enabled } = useAccountingContext();
  return useQuery({
    queryKey: user && currentCompany
      ? queryKeys.accountingAccounts(user.id, currentCompany.id)
      : ['companies', 'unavailable', 'accounting', 'accounts'] as const,
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return accountingAccounts(currentCompany.id, signal);
    },
    enabled,
    retry: false,
  });
}

export function useAccountingCategories() {
  const { user, currentCompany, enabled } = useAccountingContext();
  return useQuery({
    queryKey: user && currentCompany
      ? queryKeys.accountingCategories(user.id, currentCompany.id)
      : ['companies', 'unavailable', 'accounting', 'categories'] as const,
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return accountingCategories(currentCompany.id, signal);
    },
    enabled,
    retry: false,
  });
}

export function useAccountingEvents(options: {
  page: number;
  eventType?: AccountingEventType;
  branchId?: string;
  enabled?: boolean;
}) {
  const { user, currentCompany, enabled } = useAccountingContext();
  return useQuery({
    queryKey: user && currentCompany
      ? queryKeys.accountingEvents(user.id, currentCompany.id, options.page, options.eventType, options.branchId)
      : ['companies', 'unavailable', 'accounting', 'events', options.page] as const,
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return accountingEvents(currentCompany.id, options, signal);
    },
    enabled: enabled && options.enabled !== false,
  });
}

export function useAccountingEvent(eventId: string | null) {
  const { user, currentCompany, enabled } = useAccountingContext();
  return useQuery({
    queryKey: user && currentCompany && eventId
      ? queryKeys.accountingEvent(user.id, currentCompany.id, eventId)
      : ['companies', 'unavailable', 'accounting', 'event', eventId],
    queryFn: ({ signal }) => {
      if (!currentCompany || !eventId) throw new Error('An Accounting event is required.');
      return accountingEvent(currentCompany.id, eventId, signal);
    },
    enabled: enabled && Boolean(eventId),
    retry: false,
  });
}

export function useAccountingResult(options: {
  period: 'monthly' | 'h1' | 'h2' | 'annual';
  year: number;
  month?: number;
  branchId?: string;
  enabled?: boolean;
}) {
  const { user, currentCompany, enabled } = useAccountingContext();
  return useQuery({
    queryKey: user && currentCompany
      ? queryKeys.accountingResult(
          user.id,
          currentCompany.id,
          options.period,
          options.year,
          options.month,
          options.branchId,
        )
      : ['companies', 'unavailable', 'accounting', 'result'],
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return accountingResult(currentCompany.id, options, signal);
    },
    enabled: enabled && options.enabled !== false,
    retry: false,
  });
}

export function useAccountingMonthlyTrend(options: { branchId?: string; enabled?: boolean }) {
  const { user, currentCompany, enabled } = useAccountingContext();
  return useQuery({
    queryKey: user && currentCompany
      ? ['companies', user.id, currentCompany.id, 'accounting', 'monthly-trend', options.branchId ?? null]
      : ['companies', 'unavailable', 'accounting', 'monthly-trend'] as const,
    queryFn: ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company context is required.');
      return accountingMonthlyTrend(currentCompany.id, options.branchId, signal);
    },
    enabled: enabled && options.enabled !== false,
    retry: false,
  });
}
