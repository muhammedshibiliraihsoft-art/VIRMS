export const queryKeys = {
  authMe: ['auth', 'me'] as const,
  companies: (userId: string) => ['companies', userId] as const,
  company: (userId: string, companyId: string) => ['companies', userId, companyId] as const,
  companyModuleStates: (userId: string, companyId: string) =>
    ['companies', userId, companyId, 'module-state'] as const,
  branches: (userId: string, companyId: string, page: number) =>
    ['branches', userId, companyId, page] as const,
  branch: (userId: string, companyId: string, branchId: string) =>
    ['branches', userId, companyId, branchId] as const,
  accountingBase: (userId: string, companyId: string) =>
    ['companies', userId, companyId, 'accounting'] as const,
  accountingBranches: (userId: string, companyId: string) =>
    ['companies', userId, companyId, 'accounting', 'branches'] as const,
  accountingAccounts: (userId: string, companyId: string) =>
    ['companies', userId, companyId, 'accounting', 'accounts'] as const,
  accountingCategories: (userId: string, companyId: string) =>
    ['companies', userId, companyId, 'accounting', 'categories'] as const,
  accountingEvents: (
    userId: string,
    companyId: string,
    page: number,
    eventType?: string,
    branchId?: string,
  ) => ['companies', userId, companyId, 'accounting', 'events', page, eventType ?? 'all', branchId ?? 'all'] as const,
  accountingEvent: (userId: string, companyId: string, eventId: string) =>
    ['companies', userId, companyId, 'accounting', 'event', eventId] as const,
  accountingResult: (
    userId: string,
    companyId: string,
    period: string,
    year: number,
    month?: number,
    branchId?: string,
  ) => ['companies', userId, companyId, 'accounting', 'result', period, year, month ?? 'all', branchId ?? 'all'] as const,
};
