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
  phase5: {
    investorPortal: (userId: string, companyId: string) =>
      ['companies', userId, companyId, 'investor-portal', 'self'] as const,
    investorFundHistory: (userId: string, companyId: string) =>
      ['companies', userId, companyId, 'investor-portal', 'fund-history'] as const,
    investorInterimPaymentHistory: (userId: string, companyId: string) =>
      ['companies', userId, companyId, 'investor-portal', 'interim-payment-history'] as const,
    profitCalendarConfigurations: (userId: string, companyId: string, investorId: string) =>
      ['companies', userId, companyId, 'phase5', 'profit-calendar', investorId] as const,
    investorProfitPeriodProjection: (userId: string, companyId: string, investorId: string) =>
      ['companies', userId, companyId, 'phase8', 'investor-profit-periods', investorId] as const,
    investorPortalBinding: (userId: string, companyId: string, investorId: string) =>
      ['companies', userId, companyId, 'phase10', 'investor-portal-binding', investorId] as const,
    vehicles: (userId: string, companyId: string, page: number, branchId?: string, search?: string) =>
      ['companies', userId, companyId, 'phase5', 'vehicles', page, branchId ?? 'all', search ?? ''] as const,
    vehicle: (userId: string, companyId: string, vehicleId: string) =>
      ['companies', userId, companyId, 'phase5', 'vehicle', vehicleId] as const,
    vehicleFinancialPosition: (userId: string, companyId: string, vehicleId: string) =>
      ['companies', userId, companyId, 'phase5', 'vehicle-financial-position', vehicleId] as const,
    purchases: (userId: string, companyId: string, page: number, branchId?: string, vehicleId?: string) =>
      ['companies', userId, companyId, 'phase5', 'purchases', page, branchId ?? 'all', vehicleId ?? 'all'] as const,
    purchase: (userId: string, companyId: string, purchaseId: string) =>
      ['companies', userId, companyId, 'phase5', 'purchase', purchaseId] as const,
    expenses: (userId: string, companyId: string, vehicleId: string, page: number, branchId?: string) =>
      ['companies', userId, companyId, 'phase5', 'expenses', vehicleId, page, branchId ?? 'all'] as const,
    expense: (userId: string, companyId: string, expenseId: string) =>
      ['companies', userId, companyId, 'phase5', 'expense', expenseId] as const,
    sales: (userId: string, companyId: string, page: number, branchId?: string) =>
      ['companies', userId, companyId, 'phase5', 'sales', page, branchId ?? 'all'] as const,
    sale: (userId: string, companyId: string, saleId: string) =>
      ['companies', userId, companyId, 'phase5', 'sale', saleId] as const,
    investors: (userId: string, companyId: string, page: number) =>
      ['companies', userId, companyId, 'phase5', 'investors', page] as const,
    fundCredits: (userId: string, companyId: string, page: number, branchId?: string, investorId?: string) =>
      ['companies', userId, companyId, 'phase5', 'fund-credits', page, branchId ?? 'all', investorId ?? 'all'] as const,
    fundSummary: (userId: string, companyId: string, branchId?: string, investorId?: string) =>
      ['companies', userId, companyId, 'phase5', 'fund-summary', branchId ?? 'all', investorId ?? 'all'] as const,
    principalReturns: (userId: string, companyId: string, page: number, branchId?: string, investorId?: string) =>
      ['companies', userId, companyId, 'phase5', 'principal-returns', page, branchId ?? 'all', investorId ?? 'all'] as const,
    branches: (userId: string, companyId: string) =>
      ['companies', userId, companyId, 'phase5', 'branches'] as const,
    accounts: (userId: string, companyId: string) =>
      ['companies', userId, companyId, 'phase5', 'accounts'] as const,
    categories: (userId: string, companyId: string) =>
      ['companies', userId, companyId, 'phase5', 'income-categories'] as const,
    paymentPreference: (userId: string, companyId: string) =>
      ['companies', userId, companyId, 'phase5', 'payment-account-preference'] as const,
  },
};
