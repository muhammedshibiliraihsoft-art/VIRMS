export const queryKeys = {
  authMe: ['auth', 'me'] as const,
  companies: (userId: string) => ['companies', userId] as const,
  company: (userId: string, companyId: string) => ['companies', userId, companyId] as const,
  branches: (userId: string, companyId: string, page: number) =>
    ['branches', userId, companyId, page] as const,
  branch: (userId: string, companyId: string, branchId: string) =>
    ['branches', userId, companyId, branchId] as const,
};
