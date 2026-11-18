import React, { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Plus, RefreshCw, X } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { accountingAccounts, accountingCategories, AccountingAccount, AccountingCategory } from '../../api/accountingApi';
import { authApi } from '../../api/authApi';
import { queryKeys } from '../../api/queryKeys';
import { useCompanyModuleStates, hasCompanyBranchReadRole } from '../../api/queries';
import { phase5Api, phase5Mutation, Phase5Expense, Phase5FundCredit, Phase5FundSummary, Phase5Investor, Phase5PrincipalReturn, Phase5Purchase, Phase5Sale, Phase5SaleCorrection, Phase5Vehicle } from '../../api/phase5Api';
import { BranchListItem, BranchSummary } from '../../api/types';
import type { CompanyModuleCode } from '../../api/types';

type RouteKey = 'Stock / Investor' | 'Investor Fund' | 'Vehicle Sales' | 'Collections' | 'Sale Corrections & Refunds' | 'Running Capital';
type FormKind =
  | 'vehicle' | 'purchase' | 'purchasePayment' | 'purchaseRefund' | 'purchaseCorrection'
  | 'expense' | 'expensePayment' | 'expenseRefund' | 'expenseCorrection' | 'sale'
  | 'saleReceipt' | 'saleRefund' | 'saleCorrection' | 'investor' | 'investorEdit' | 'fundCredit' | 'fundCreditCorrection' | 'principalReturn' | 'vehicleMove';
type FormAction = { kind: FormKind; targetId?: string };
type FieldType = 'text' | 'money' | 'datetime' | 'select';
interface FieldOption { value: string; label: string }
interface FieldSpec { key: string; label: string; type: FieldType; required?: boolean; options?: FieldOption[]; help?: string; placeholder?: string }
interface FormCommand { module: 'investment' | 'vehicle-management'; suffix: string; body: Record<string, unknown>; method?: 'POST' | 'PATCH' }

const PHASE5_ROOT = ['phase5'] as const;
const VEHICLE_MODULE = 'vehicle_management';
const INVESTMENT_MODULE = 'investment';
const ACCOUNTING_MODULE = 'accounting';

function localDateTime(): string {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function toIso(value: string): string {
  return value ? new Date(value).toISOString() : new Date().toISOString();
}

function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '₹0.00';
  const [rawWhole, decimals = '00'] = String(value).replace(/,/g, '').split('.');
  const negative = rawWhole.startsWith('-');
  const whole = negative ? rawWhole.slice(1) : rawWhole;
  const tail = whole.slice(-3);
  const head = whole.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',');
  return `₹${negative ? '-' : ''}${head ? `${head},` : ''}${tail}.${decimals.padEnd(2, '0').slice(0, 2)}`;
}

function displayDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(parsed);
}

function displayDateTime(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(parsed);
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : 'The request could not be completed. Try again.';
}

function isCompanyAccountant(company: { company_wide_roles?: string[] } | null): boolean {
  return Boolean(company?.company_wide_roles?.includes('accountant'));
}

function moneyCents(value: string): bigint {
  const normalized = value.trim().replace(/,/g, '');
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(normalized);
  if (!match) throw new Error('Enter a valid amount with up to two decimal places.');
  return BigInt(match[1]) * 100n + BigInt((match[2] ?? '').padEnd(2, '0'));
}

function moneyFromCents(value: bigint): string {
  if (value < 0n) throw new Error('The amount cannot be negative.');
  return `${value / 100n}.${String(value % 100n).padStart(2, '0')}`;
}

function isPositiveMoney(value: string): boolean {
  try { return moneyCents(value) > 0n; } catch { return false; }
}

function PageControls({ page, hasPrevious, hasNext, onChange }: { page: number; hasPrevious: boolean; hasNext: boolean; onChange: (page: number) => void }) {
  if (!hasPrevious && !hasNext) return null;
  return (
    <div className="mt-3 flex items-center justify-end gap-2 text-xs">
      <button type="button" disabled={!hasPrevious} onClick={() => onChange(Math.max(1, page - 1))} className="inline-flex h-8 items-center gap-1 rounded-lg border border-[#e2d8ce] px-2.5 font-semibold disabled:opacity-40 dark:border-zinc-700">
        <ChevronLeft className="h-3.5 w-3.5" /> Previous
      </button>
      <span className="min-w-14 text-center text-gray-500">Page {page}</span>
      <button type="button" disabled={!hasNext} onClick={() => onChange(page + 1)} className="inline-flex h-8 items-center gap-1 rounded-lg border border-[#e2d8ce] px-2.5 font-semibold disabled:opacity-40 dark:border-zinc-700">
        Next <ChevronRight className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export const Phase5WorkspaceView: React.FC<{ routeKey: RouteKey }> = ({ routeKey }) => {
  const { status, user, currentCompany } = useAuth();
  const queryClient = useQueryClient();
  const moduleQuery = useCompanyModuleStates();
  const canRead = status === 'authenticated' && Boolean(currentCompany) && hasCompanyBranchReadRole(user);
  const companyAccountant = isCompanyAccountant(currentCompany);
  const [branchId, setBranchId] = useState('');
  const [page, setPage] = useState(1);
  const [returnsPage, setReturnsPage] = useState(1);
  const [detailPage, setDetailPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null);
  const [investorFilterId, setInvestorFilterId] = useState('');
  const [formAction, setFormAction] = useState<FormAction | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [search]);

  const isFundRoute = routeKey === 'Investor Fund';
  const isVehicleRoute = routeKey === 'Stock / Investor' || routeKey === 'Running Capital';
  const isSalesRoute = routeKey === 'Vehicle Sales' || routeKey === 'Collections' || routeKey === 'Sale Corrections & Refunds';
  const needsVehicleList = isVehicleRoute;
  const states = new Map((moduleQuery.data?.modules ?? []).map((row) => [row.code, row.state]));
  const moduleOn = (code: CompanyModuleCode) => states.get(code) === 'enabled';
  const investmentOn = moduleOn(INVESTMENT_MODULE);

  const branchQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.branches(user.id, currentCompany.id) : ['companies', 'unavailable', ...PHASE5_ROOT, 'branches'],
    queryFn: async ({ signal }) => {
      if (!currentCompany) throw new Error('A single authorized Company is required.');
      const result: BranchListItem[] = [];
      let pageNumber = 1;
      let pageResult = await authApi.phase5Branches(currentCompany.id, pageNumber, signal);
      result.push(...pageResult.results);
      while (pageResult.next) {
        pageNumber += 1;
        pageResult = await authApi.phase5Branches(currentCompany.id, pageNumber, signal);
        result.push(...pageResult.results);
      }
      return result;
    },
    enabled: canRead && (companyAccountant || Boolean(currentCompany?.branches_truncated)),
    retry: false,
  });
  const branches: Array<BranchSummary | BranchListItem> = companyAccountant || currentCompany?.branches_truncated
    ? branchQuery.data ?? []
    : currentCompany?.branches ?? [];
  const branchOptions: FieldOption[] = branches.map((branch) => ({ value: branch.id, label: branch.name }));
  const purchaseNeedsAccount = formAction?.kind === 'purchase' && isPositiveMoney(formValues.initial_payment_amount ?? '0.00');
  const needsCashAccount = Boolean(formAction && (
    ['purchasePayment', 'purchaseRefund', 'expensePayment', 'expenseRefund', 'saleReceipt', 'saleRefund', 'fundCredit', 'principalReturn'].includes(formAction.kind) || purchaseNeedsAccount
  ));

  const accountsQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.accounts(user.id, currentCompany.id) : ['companies', 'unavailable', ...PHASE5_ROOT, 'accounts'],
    queryFn: ({ signal }) => currentCompany ? accountingAccounts(currentCompany.id, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && moduleOn(ACCOUNTING_MODULE) && needsCashAccount,
    retry: false,
  });
  const preferenceQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.paymentPreference(user.id, currentCompany.id) : ['companies', 'unavailable', ...PHASE5_ROOT, 'payment-account-preference'],
    queryFn: ({ signal }) => currentCompany ? phase5Api.paymentAccountPreference(currentCompany.id, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && moduleOn(ACCOUNTING_MODULE) && needsCashAccount,
    retry: false,
  });
  const investorsQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.investors(user.id, currentCompany.id, 1) : ['companies', 'unavailable', ...PHASE5_ROOT, 'investors'],
    queryFn: async ({ signal }) => {
      if (!currentCompany) throw new Error('A Company is required.');
      let pageNumber = 1;
      let result = await phase5Api.investors(currentCompany.id, pageNumber, signal);
      const investors = [...result.results];
      while (result.next) {
        result = await phase5Api.investors(currentCompany.id, ++pageNumber, signal);
        investors.push(...result.results);
      }
      return investors;
    },
    enabled: canRead && (isFundRoute || Boolean(formAction && ['purchase', 'expense', 'fundCredit', 'fundCreditCorrection', 'principalReturn'].includes(formAction.kind))),
    retry: false,
  });
  const vehiclesQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.vehicles(user.id, currentCompany.id, page, branchId || undefined, debouncedSearch || undefined) : ['companies', 'unavailable', ...PHASE5_ROOT, 'vehicles'],
    queryFn: ({ signal }) => currentCompany ? phase5Api.vehicles(currentCompany.id, { page, branchId: branchId || undefined, search: debouncedSearch || undefined }, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && needsVehicleList,
    retry: false,
  });
  const purchasesQuery = useQuery({
    queryKey: currentCompany && user && selectedVehicleId ? queryKeys.phase5.purchases(user.id, currentCompany.id, 1, undefined, selectedVehicleId) : ['companies', 'unavailable', ...PHASE5_ROOT, 'purchase', selectedVehicleId],
    queryFn: ({ signal }) => currentCompany && selectedVehicleId ? phase5Api.purchases(currentCompany.id, { page: 1, vehicleId: selectedVehicleId }, signal) : Promise.reject(new Error('A Vehicle is required.')),
    enabled: canRead && Boolean(selectedVehicleId) && (isVehicleRoute || formAction?.kind === 'sale'),
    retry: false,
  });
  const expensesQuery = useQuery({
    queryKey: currentCompany && user && selectedVehicleId ? queryKeys.phase5.expenses(user.id, currentCompany.id, selectedVehicleId, detailPage, branchId || undefined) : ['companies', 'unavailable', ...PHASE5_ROOT, 'expenses', selectedVehicleId],
    queryFn: ({ signal }) => currentCompany && selectedVehicleId ? phase5Api.expenses(currentCompany.id, selectedVehicleId, { page: detailPage, branchId: branchId || undefined }, signal) : Promise.reject(new Error('A Vehicle is required.')),
    enabled: canRead && Boolean(selectedVehicleId) && isVehicleRoute,
    retry: false,
  });
  const salesQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.sales(user.id, currentCompany.id, page, branchId || undefined) : ['companies', 'unavailable', ...PHASE5_ROOT, 'sales'],
    queryFn: ({ signal }) => currentCompany ? phase5Api.sales(currentCompany.id, { page, branchId: branchId || undefined }, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && isSalesRoute,
    retry: false,
  });
  const selectedSaleId = vehiclesQuery.data?.results.find((vehicle) => vehicle.id === selectedVehicleId)?.sale_id ?? null;
  const saleDetailQuery = useQuery({
    queryKey: currentCompany && user && selectedSaleId ? queryKeys.phase5.sale(user.id, currentCompany.id, selectedSaleId) : ['companies', 'unavailable', ...PHASE5_ROOT, 'sale-detail'],
    queryFn: ({ signal }) => currentCompany && selectedSaleId ? phase5Api.sale(currentCompany.id, selectedSaleId, signal) : Promise.reject(new Error('A Sale is required.')),
    enabled: canRead && Boolean(selectedSaleId) && isVehicleRoute,
    retry: false,
  });
  const investors = investorsQuery.data ?? [];
  const accounts = (accountsQuery.data ?? []) as AccountingAccount[];
  const vehicles = vehiclesQuery.data?.results ?? [];
  const selectedVehicle = vehicles.find((vehicle) => vehicle.id === selectedVehicleId) ?? null;
  const purchase = purchasesQuery.data?.results[0] ?? null;
  const expenses = expensesQuery.data?.results ?? [];
  const sales = salesQuery.data?.results ?? [];
  const expenseRefundExpense = formAction?.kind === 'expenseRefund'
    ? expenses.find((expense) => expense.id === formAction.targetId) ?? null
    : null;
  const refundHasExcess = (() => {
    if (!expenseRefundExpense || formAction?.kind !== 'expenseRefund') return false;
    try { return moneyCents(formValues.amount ?? '0.00') > moneyCents(expenseRefundExpense.net_paid); } catch { return false; }
  })();
  const refundExcessAmount = (() => {
    if (!refundHasExcess || !expenseRefundExpense) return null;
    try {
      return moneyFromCents(moneyCents(formValues.amount ?? '0.00') - moneyCents(expenseRefundExpense.net_paid));
    } catch {
      return null;
    }
  })();
  const categoriesQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.categories(user.id, currentCompany.id) : ['companies', 'unavailable', ...PHASE5_ROOT, 'income-categories'],
    queryFn: ({ signal }) => currentCompany ? accountingCategories(currentCompany.id, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && moduleOn(ACCOUNTING_MODULE) && refundHasExcess,
    retry: false,
  });
  const incomeCategories = ((categoriesQuery.data ?? []) as AccountingCategory[]).filter((category) => category.kind === 'INCOME' && category.is_active);
  const allowedInvestorId = purchase?.investor_id ?? expenses.find((expense) => expense.investor_id)?.investor_id ?? '';
  const visibleInvestors = allowedInvestorId ? investors.filter((investor) => investor.id === allowedInvestorId) : investors;

  const fundCreditsQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.fundCredits(user.id, currentCompany.id, page, branchId || undefined, investorFilterId || undefined) : ['companies', 'unavailable', ...PHASE5_ROOT, 'fund-credits'],
    queryFn: ({ signal }) => currentCompany ? phase5Api.fundCredits(currentCompany.id, { page, branchId: branchId || undefined, investorId: investorFilterId || undefined }, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && isFundRoute,
    retry: false,
  });
  const fundSummaryQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.fundSummary(user.id, currentCompany.id, branchId || undefined, investorFilterId || undefined) : ['companies', 'unavailable', ...PHASE5_ROOT, 'fund-summary'],
    queryFn: ({ signal }) => currentCompany ? phase5Api.fundSummary(currentCompany.id, { branchId: branchId || undefined, investorId: investorFilterId || undefined }, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && isFundRoute,
    retry: false,
  });
  const returnsQuery = useQuery({
    queryKey: currentCompany && user ? queryKeys.phase5.principalReturns(user.id, currentCompany.id, returnsPage, branchId || undefined, investorFilterId || undefined) : ['companies', 'unavailable', ...PHASE5_ROOT, 'principal-returns'],
    queryFn: ({ signal }) => currentCompany ? phase5Api.principalReturns(currentCompany.id, { page: returnsPage, branchId: branchId || undefined, investorId: investorFilterId || undefined }, signal) : Promise.reject(new Error('A Company is required.')),
    enabled: canRead && isFundRoute,
    retry: false,
  });

  const startForm = (kind: FormKind, targetId?: string) => {
    setMessage(null);
    setFormAction({ kind, targetId });
    const defaults: Record<string, string> = { effective_at: localDateTime(), sold_at: localDateTime(), amount: '', purchase_cost: '', sale_price: '', investor_fund_amount: '0.00', initial_payment_amount: '0.00' };
    if (kind === 'vehicle') defaults.branch_id = branchId || branches[0]?.id || '';
    if (kind === 'fundCredit' || kind === 'principalReturn') {
      defaults.branch_id = branchId || branches[0]?.id || '';
      defaults.investor_id = targetId || investorFilterId || '';
      defaults.account_id = preferenceQuery.data?.account_id ?? '';
    }
    if (kind === 'investorEdit') defaults.name = investors.find((row) => row.id === targetId)?.name ?? '';
    if (kind === 'purchase' || kind === 'expense') {
      defaults.investor_id = allowedInvestorId || '';
      defaults.account_id = preferenceQuery.data?.account_id ?? '';
    }
    if (['purchasePayment', 'purchaseRefund', 'expensePayment', 'expenseRefund', 'saleReceipt', 'saleRefund'].includes(kind)) {
      defaults.account_id = preferenceQuery.data?.account_id ?? '';
    }
    setFormValues(defaults);
  };
  const closeForm = () => { setFormAction(null); setFormValues({}); };

  const refundDestinationBlocked = formAction?.kind === 'expenseRefund' && refundHasExcess && (
    categoriesQuery.isLoading || Boolean(categoriesQuery.error) || incomeCategories.length === 0 ||
    !formValues.excess_income_category_id || !formValues.excess_income_description?.trim()
  );

  useEffect(() => {
    if (!formAction || !preferenceQuery.data?.account_id) return;
    if (!['purchase', 'purchasePayment', 'purchaseRefund', 'expensePayment', 'expenseRefund', 'saleReceipt', 'saleRefund', 'fundCredit', 'principalReturn'].includes(formAction.kind)) return;
    setFormValues((previous) => previous.account_id ? previous : { ...previous, account_id: preferenceQuery.data.account_id ?? '' });
  }, [formAction, preferenceQuery.data?.account_id]);

  const mutation = useMutation({
    mutationFn: async ({ action, values }: { action: FormAction; values: Record<string, string> }) => {
      if (!currentCompany || !user) throw new Error('An authenticated Company session is required.');
      const command = buildCommand(action, values, { selectedVehicle, purchase, expenses, sales, saleDetail: saleDetailQuery.data ?? null, investors, investorFilterId, branches, companyAccountant });
      return phase5Mutation<unknown>(currentCompany.id, user.id, command.module, command.suffix, command.body, command.method ?? 'POST');
    },
    onSuccess: async () => {
      if (!currentCompany || !user) return;
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['companies', user.id, currentCompany.id, 'phase5'] }),
        queryClient.invalidateQueries({ queryKey: queryKeys.accountingBase(user.id, currentCompany.id) }),
      ]);
      setMessage('Saved successfully. The latest server records are refreshing.');
      closeForm();
    },
  });

  const formFields = formAction ? fieldsForAction(formAction, {
    branches: branchOptions,
    accounts,
    investors: formAction.kind === 'fundCreditCorrection' ? investors : visibleInvestors,
    vehicles,
    sale: saleDetailQuery.data ?? sales.find((item) => item.id === formAction.targetId) ?? null,
    expense: expenses.find((item) => item.id === formAction.targetId) ?? null,
    fundCredit: fundCreditsQuery.data?.results.find((item) => item.id === formAction.targetId) ?? null,
    incomeCategories,
    companyAccountant,
    investmentOn,
    initialPaymentAmount: formValues.initial_payment_amount ?? '0.00',
    investorFundAmount: formValues.investor_fund_amount ?? '0.00',
    refundAmount: formValues.amount ?? '0.00',
  }) : [];

  const moduleRows: Array<{ code: CompanyModuleCode; label: string }> = [
    { code: VEHICLE_MODULE, label: 'Vehicles' },
    { code: INVESTMENT_MODULE, label: 'Investment' },
    { code: ACCOUNTING_MODULE, label: 'Accounting' },
  ];
  const allModuleStatesLoaded = Boolean(moduleQuery.data);
  const headerCopy: Record<RouteKey, { title: string; subtitle: string }> = {
    'Stock / Investor': { title: 'Stock / Investor Vehicles', subtitle: 'Backend vehicle register, purchase funding, direct vehicle costs and sales.' },
    'Investor Fund': { title: 'Investor Fund', subtitle: 'Company-wide investor profiles and branch-tagged fund records.' },
    'Vehicle Sales': { title: 'Vehicle Sales', subtitle: 'Confirmed sales and the current buyer balance for each vehicle.' },
    'Collections': { title: 'Collections', subtitle: 'Record actual buyer receipts against confirmed sales.' },
    'Sale Corrections & Refunds': { title: 'Sale Corrections & Refunds', subtitle: 'Record buyer refunds and audited sale-price corrections.' },
    'Running Capital': { title: 'Running Capital', subtitle: 'Inspect Company Running Capital allocations recorded against each stock vehicle.' },
  };
  const currentPage = isFundRoute ? fundCreditsQuery.data : isSalesRoute ? salesQuery.data : vehiclesQuery.data;
  const isLoading = moduleQuery.isLoading || (isFundRoute ? fundCreditsQuery.isLoading || investorsQuery.isLoading : isSalesRoute ? salesQuery.isLoading : isVehicleRoute ? vehiclesQuery.isLoading : false);
  const pageError = moduleQuery.error || (isFundRoute ? fundCreditsQuery.error || investorsQuery.error || fundSummaryQuery.error || returnsQuery.error : isSalesRoute ? salesQuery.error : isVehicleRoute ? vehiclesQuery.error || (selectedVehicleId ? purchasesQuery.error || expensesQuery.error || saleDetailQuery.error : null) : null);

  return (
    <div className="flex flex-col gap-3.5 sm:gap-4 animate-in fade-in duration-150">
      <div className="flex flex-col gap-3 border-b border-[#f2ebe5] pb-3 dark:border-zinc-800 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-gray-950 dark:text-white sm:text-2xl">{headerCopy[routeKey].title}</h1>
          <p className="mt-1 text-xs font-medium text-gray-500 dark:text-gray-400">{headerCopy[routeKey].subtitle}</p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {moduleRows.map((row) => (
            <span key={row.code} className={`rounded-full border px-2 py-1 text-[10px] font-bold ${moduleOn(row.code) ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-300' : 'border-gray-200 bg-gray-50 text-gray-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400'}`}>
              {row.label}: {allModuleStatesLoaded ? (moduleOn(row.code) ? 'ON' : 'OFF') : '…'}
            </span>
          ))}
        </div>
      </div>

      {!canRead && <Notice tone="error">A single authorized Company and Accountant/Owner/Media read role are required to load this workspace.</Notice>}
      {currentCompany?.branches_truncated && branchQuery.isLoading && <Notice>Loading your authorized Branch list…</Notice>}
      {currentCompany?.branches_truncated && branchQuery.error && <Notice tone="error">{errorText(branchQuery.error)}</Notice>}
      {pageError && <Notice tone="error">{errorText(pageError)}</Notice>}
      {message && <Notice tone="success">{message}</Notice>}

      {formAction && (
        <form onSubmit={(event) => { event.preventDefault(); mutation.mutate({ action: formAction, values: formValues }); }} className="rounded-2xl border border-[#e2d8ce] bg-white p-3 shadow-sm dark:border-zinc-700 dark:bg-zinc-900 sm:p-4">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-extrabold text-gray-950 dark:text-white">{formTitle(formAction.kind)}</h2>
              <p className="mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">{formHelp(formAction.kind)}</p>
            </div>
            <button type="button" aria-label="Close form" onClick={closeForm} className="rounded-full p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800"><X className="h-4 w-4" /></button>
          </div>
          {mutation.error && <Notice tone="error">{errorText(mutation.error)}</Notice>}
          {formAction.kind === 'expenseRefund' && refundHasExcess && categoriesQuery.isLoading && (
            <Notice>Loading Company Income categories…</Notice>
          )}
          {formAction.kind === 'expenseRefund' && refundHasExcess && categoriesQuery.error && (
            <div className="flex flex-wrap items-center gap-2">
              <Notice tone="error">Could not load Company Income categories. Retry before saving.</Notice>
              <button type="button" onClick={() => categoriesQuery.refetch()} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[11px] font-semibold dark:border-zinc-700">Retry</button>
            </div>
          )}
          {formAction.kind === 'expenseRefund' && refundHasExcess && !categoriesQuery.isLoading && !categoriesQuery.error && incomeCategories.length === 0 && (
            <Notice tone="error">Create an active Company Income category before recording the excess as Income.</Notice>
          )}
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {formFields.map((field) => (
              <label key={field.key} className="flex min-w-0 flex-col gap-1 text-[11px] font-bold text-gray-600 dark:text-gray-300">
                <span>{field.label}{field.required ? ' *' : ''}</span>
                {field.type === 'select' ? (
                  <select required={field.required} value={formValues[field.key] ?? ''} onChange={(event) => setFormValues((previous) => ({ ...previous, [field.key]: event.target.value }))} className="h-10 min-w-0 rounded-lg border border-[#e2d8ce] bg-white px-2.5 text-xs font-medium text-gray-900 outline-none focus:border-[var(--theme-primary)] dark:border-zinc-700 dark:bg-zinc-950 dark:text-white">
                    <option value="">Select…</option>
                    {(field.options ?? []).map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                ) : (
                  <input required={field.required} type={field.type === 'money' ? 'text' : field.type === 'datetime' ? 'datetime-local' : 'text'} inputMode={field.type === 'money' ? 'decimal' : undefined} maxLength={field.type === 'text' ? 500 : undefined} placeholder={field.placeholder} value={formValues[field.key] ?? ''} onChange={(event) => setFormValues((previous) => ({ ...previous, [field.key]: event.target.value }))} className="h-10 min-w-0 rounded-lg border border-[#e2d8ce] bg-white px-2.5 text-xs font-medium text-gray-900 outline-none focus:border-[var(--theme-primary)] dark:border-zinc-700 dark:bg-zinc-950 dark:text-white" />
                )}
                {field.help && <span className="font-medium leading-4 text-gray-400">{field.help}</span>}
              </label>
            ))}
          </div>
          {formAction.kind === 'expenseRefund' && refundHasExcess && refundExcessAmount && (
            <p role="status" className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
              Excess {formatMoney(refundExcessAmount)} will be recorded as a new Company Income entry with its own category and note. The actual refund remains one Cash/Bank receipt.
            </p>
          )}
          {(formAction.kind === 'purchase' || formAction.kind === 'expense') && (
            <p className="mt-2 text-[11px] text-gray-500 dark:text-gray-400">Company Running Capital is calculated as the full amount minus Investor Fund. Each source must total the recorded cost.</p>
          )}
          <div className="mt-3 flex items-center justify-end gap-2">
            <button type="button" onClick={closeForm} className="h-9 rounded-lg px-3 text-xs font-bold text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-zinc-800">Cancel</button>
            <button type="submit" disabled={mutation.isPending || !allModuleStatesLoaded || Boolean(refundDestinationBlocked)} className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#18181b] px-3.5 text-xs font-bold text-white disabled:cursor-wait disabled:opacity-60 dark:bg-white dark:text-black">
              {mutation.isPending ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : null}{mutation.isPending ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      )}

      {isFundRoute ? (
        <FundPanel
          summary={fundSummaryQuery.data}
          credits={fundCreditsQuery.data?.results ?? []}
          returns={returnsQuery.data?.results ?? []}
          investors={investors}
          branches={branches}
          branchId={branchId}
          onBranch={(value) => { setBranchId(value); setPage(1); setReturnsPage(1); }}
          selectedInvestorId={investorFilterId}
          onInvestorFilter={(value) => { setInvestorFilterId(value); setPage(1); setReturnsPage(1); }}
          onAddInvestor={() => startForm('investor')}
          onEditInvestor={(investor) => startForm('investorEdit', investor.id)}
          onCredit={(investorId) => startForm('fundCredit', investorId)}
          onCorrectCredit={(credit) => startForm('fundCreditCorrection', credit.id)}
          onReturn={(investorId) => startForm('principalReturn', investorId)}
          page={page}
          hasPrevious={Boolean(currentPage?.previous)}
          hasNext={Boolean(currentPage?.next)}
          onPage={setPage}
          returnPage={returnsPage}
          returnHasPrevious={Boolean(returnsQuery.data?.previous)}
          returnHasNext={Boolean(returnsQuery.data?.next)}
          onReturnPage={setReturnsPage}
          canProfileWrite={allModuleStatesLoaded && investmentOn}
          canFundWrite={allModuleStatesLoaded && investmentOn && moduleOn(ACCOUNTING_MODULE)}
          canCreditCorrection={allModuleStatesLoaded && investmentOn}
          companyAccountant={companyAccountant}
        />
      ) : isSalesRoute ? (
        <SalesPanel
          routeKey={routeKey}
          sales={sales}
          branches={branches}
          branchId={branchId}
          onBranch={(value) => { setBranchId(value); setPage(1); }}
          onReceipt={(sale) => startForm('saleReceipt', sale.id)}
          onRefund={(sale) => startForm('saleRefund', sale.id)}
          onCorrection={(sale) => startForm('saleCorrection', sale.id)}
          page={page}
          hasPrevious={Boolean(currentPage?.previous)}
          hasNext={Boolean(currentPage?.next)}
          onPage={setPage}
          canRead={canRead}
          canVehicleWrite={allModuleStatesLoaded && moduleOn(VEHICLE_MODULE)}
          canAccountingWrite={allModuleStatesLoaded && moduleOn(ACCOUNTING_MODULE)}
          canInvestmentWrite={allModuleStatesLoaded && investmentOn}
        />
      ) : (
        <VehiclePanel
          routeKey={routeKey}
          vehicles={vehicles}
          selectedVehicle={selectedVehicle}
          purchase={purchase}
          expenses={expenses}
          sale={saleDetailQuery.data ?? null}
          branches={branches}
          branchId={branchId}
          search={search}
          onSearch={(value) => { setSearch(value); setPage(1); setSelectedVehicleId(null); }}
          onBranch={(value) => { setBranchId(value); setPage(1); setDetailPage(1); setSelectedVehicleId(null); }}
          onSelectVehicle={(vehicle) => { setSelectedVehicleId((current) => current === vehicle.id ? null : vehicle.id); setDetailPage(1); setPage(1); }}
          onAddVehicle={() => startForm('vehicle')}
          onPurchase={(vehicle) => { setSelectedVehicleId(vehicle.id); startForm('purchase', vehicle.id); }}
          onAddExpense={(vehicle) => { setSelectedVehicleId(vehicle.id); startForm('expense', vehicle.id); }}
          onPurchasePayment={(item) => startForm('purchasePayment', item.id)}
          onPurchaseRefund={(item) => startForm('purchaseRefund', item.id)}
          onPurchaseCorrection={(item) => startForm('purchaseCorrection', item.id)}
          onExpensePayment={(item) => startForm('expensePayment', item.id)}
          onExpenseRefund={(item) => startForm('expenseRefund', item.id)}
          onExpenseCorrection={(item) => startForm('expenseCorrection', item.id)}
          onSale={(vehicle) => startForm('sale', vehicle.id)}
          onSaleReceipt={(item) => startForm('saleReceipt', item.id)}
          onSaleRefund={(item) => startForm('saleRefund', item.id)}
          onSaleCorrection={(item) => startForm('saleCorrection', item.id)}
          onMove={(vehicle) => startForm('vehicleMove', vehicle.id)}
          page={page}
          hasPrevious={Boolean(vehiclesQuery.data?.previous)}
          hasNext={Boolean(vehiclesQuery.data?.next)}
          onPage={setPage}
          loading={isLoading}
          canVehicleWrite={allModuleStatesLoaded && moduleOn(VEHICLE_MODULE)}
          canAccountingWrite={allModuleStatesLoaded && moduleOn(ACCOUNTING_MODULE)}
          canInvestmentWrite={allModuleStatesLoaded && moduleOn(INVESTMENT_MODULE)}
          companyAccountant={companyAccountant}
          detailLoading={Boolean(selectedVehicleId) && (purchasesQuery.isLoading || expensesQuery.isLoading || saleDetailQuery.isLoading)}
          detailPage={detailPage}
          detailHasPrevious={Boolean(expensesQuery.data?.previous)}
          detailHasNext={Boolean(expensesQuery.data?.next)}
          expenseRunningCapitalTotal={purchasesQuery.isSuccess && expensesQuery.isSuccess ? expensesQuery.data?.running_capital_total : undefined}
          onDetailPage={setDetailPage}
        />
      )}
    </div>
  );
};

function formTitle(kind: FormKind): string {
  const titles: Record<FormKind, string> = {
    vehicle: 'Register stock vehicle', purchase: 'Record vehicle purchase', purchasePayment: 'Pay seller installment', purchaseRefund: 'Record seller refund', purchaseCorrection: 'Correct purchase cost',
    expense: 'Add vehicle expense', expensePayment: 'Pay vehicle expense installment', expenseRefund: 'Record expense refund', expenseCorrection: 'Correct vehicle expense', sale: 'Confirm vehicle sale',
    saleReceipt: 'Record buyer receipt', saleRefund: 'Record buyer refund', saleCorrection: 'Correct sale price', investor: 'Create investor profile', investorEdit: 'Edit investor profile', fundCredit: 'Record investor fund credit', fundCreditCorrection: 'Correct Fund Credit Investor', principalReturn: 'Return unused principal', vehicleMove: 'Move vehicle to another Branch',
  };
  return titles[kind];
}

function formHelp(kind: FormKind): string {
  if (kind === 'purchase') return 'The vehicle cost and funding sources are saved once; seller payments are separate records.';
  if (kind === 'expense') return 'Record a vehicle-linked cost. Any actual payment is entered separately.';
  if (kind === 'expenseRefund') return 'Record the full money received once. Any excess is a separate Company Income entry with its own category and note.';
  if (kind === 'purchaseCorrection' || kind === 'expenseCorrection' || kind === 'saleCorrection') return 'The server validates paid/refunded amounts and records an audited correction.';
  if (kind === 'fundCredit') return 'One actual bank transfer or cash receipt belongs to one Investor Fund Credit.';
  if (kind === 'fundCreditCorrection') return 'The original credit and Cash/Bank movement stay unchanged. If the credit was used or returned, review the related Investor calculations manually.';
  if (kind === 'principalReturn') return 'Only unused Investor principal can be returned. The server allocates the return using the credit ledger.';
  return 'The server validates Company scope, module availability and the financial limits before saving.';
}

function fieldsForAction(kind: FormAction, context: {
  branches: FieldOption[]; accounts: AccountingAccount[]; investors: Phase5Investor[]; vehicles: Phase5Vehicle[];
  sale: Phase5Sale | null; expense: Phase5Expense | null; fundCredit: Phase5FundCredit | null; incomeCategories: AccountingCategory[]; companyAccountant: boolean; investmentOn: boolean;
  initialPaymentAmount: string; investorFundAmount: string; refundAmount: string;
}): FieldSpec[] {
  const branchFields: FieldSpec[] = [{ key: 'branch_id', label: 'Branch', type: 'select', required: true, options: context.branches }];
  const accountFields: FieldSpec[] = [{ key: 'account_id', label: 'Cash / Bank account', type: 'select', required: true, options: context.accounts.filter((account) => account.is_active).map((account) => ({ value: account.id, label: `${account.label} · ${account.account_type}` })), help: 'Your last successfully saved account is selected automatically when available.' }];
  const fundUsed = (value: string) => {
    try { return moneyCents(value) > 0n; } catch { return false; }
  };
  const investorFields: FieldSpec[] = [{ key: 'investor_id', label: 'Investor', type: 'select', required: fundUsed(context.investorFundAmount), options: context.investors.map((investor) => ({ value: investor.id, label: investor.name })) }];
  const purchasePaymentFields = fundUsed(context.initialPaymentAmount) ? accountFields : [];
  const refundExcess = kind.kind === 'expenseRefund' && context.expense !== null && (() => {
    try { return moneyCents(context.refundAmount) > moneyCents(context.expense.net_paid); } catch { return false; }
  })();
  const money = (key: string, label: string, required = true): FieldSpec => ({ key, label, type: 'money', required, placeholder: '0.00' });
  const date = (key = 'effective_at', label = 'Effective date and time'): FieldSpec => ({ key, label, type: 'datetime' });
  const text = (key: string, label: string, required = true, help?: string): FieldSpec => ({ key, label, type: 'text', required, help });
  switch (kind.kind) {
    case 'vehicle': return [text('registration', 'Registration'), text('model', 'Model / description'), ...branchFields];
    case 'purchase': return [money('purchase_cost', 'Purchase cost'), text('seller_name', 'Seller name'), text('seller_phone', 'Seller phone', false), ...(context.companyAccountant && context.investmentOn ? [...investorFields, money('investor_fund_amount', 'Investor Fund allocation', false)] : []), money('initial_payment_amount', 'Initial seller payment (0 allowed)', false), ...purchasePaymentFields, date('purchased_at', 'Purchase date')];
    case 'purchasePayment': return [...accountFields, money('amount', 'Installment amount'), text('reference', 'Reference', false), date()];
    case 'purchaseRefund': return [...accountFields, money('amount', 'Refund received'), date()];
    case 'purchaseCorrection': return [money('purchase_cost', 'Corrected purchase cost'), text('reason', 'Reason')];
    case 'expense': return [money('amount', 'Total vehicle expense'), text('description', 'Expense description'), ...(context.companyAccountant && context.investmentOn ? [{ key: 'investor_id', label: 'Investor', type: 'select' as const, options: context.investors.map((investor) => ({ value: investor.id, label: investor.name })), help: 'Available Investor Fund is used first; Company Running Capital covers the balance.' }] : []), date()];
    case 'expensePayment': return [...accountFields, money('amount', 'Installment amount'), text('reference', 'External reference (bank ID / cash voucher)'), date()];
    case 'expenseRefund': {
      const fields: FieldSpec[] = [...accountFields, money('amount', 'Actual refund received')];
      if (!refundExcess) return [...fields, date()];
      fields.push(
        { key: 'excess_income_category_id', label: 'New Company Income category', type: 'select', required: true, options: context.incomeCategories.map((category) => ({ value: category.id, label: category.label })) },
        text('excess_income_description', 'New Income description', true, 'The separate Income record is created explicitly; the actual refund remains one Cash/Bank receipt.'),
      );
      return [...fields, date()];
    }
    case 'expenseCorrection': return [money('amount', 'Corrected expense amount'), text('reason', 'Reason')];
    case 'sale': return [money('sale_price', 'Sale price'), text('buyer_name', 'Buyer name'), text('buyer_phone', 'Buyer phone'), date('sold_at', 'Sale date and time')];
    case 'saleReceipt': return [...accountFields, money('amount', 'Buyer payment amount'), text('reference', 'External reference (bank ID / cash voucher)'), date()];
    case 'saleRefund': return [...accountFields, money('amount', `Refund (up to ${formatMoney(context.sale?.refund_payable ?? '0.00')})`), date()];
    case 'saleCorrection': return [money('sale_price', 'Corrected sale price'), text('reason', 'Reason')];
    case 'investor': return [text('name', 'Investor name')];
    case 'investorEdit': return [text('name', 'Investor name')];
    case 'fundCredit': return [...investorFields, ...branchFields, ...accountFields, money('amount', 'Amount'), text('reference', 'External reference (bank ID / cash voucher)'), date()];
    case 'fundCreditCorrection': return [
      { key: 'to_investor_id', label: 'Correct Investor', type: 'select', required: true, options: context.investors.filter((investor) => investor.id !== context.fundCredit?.investor_id).map((investor) => ({ value: investor.id, label: investor.name })) },
      text('reason', 'Correction reason'),
    ];
    case 'principalReturn': return [...investorFields, ...branchFields, ...accountFields, money('amount', 'Principal returned'), text('reference', 'External reference'), date()];
    case 'vehicleMove': return [{ key: 'to_branch_id', label: 'Destination Branch', type: 'select', required: true, options: context.branches }, text('reason', 'Reason')];
    default: return [];
  }
}

function buildCommand(action: FormAction, values: Record<string, string>, context: {
  selectedVehicle: Phase5Vehicle | null; purchase: Phase5Purchase | null; expenses: Phase5Expense[]; sales: Phase5Sale[]; saleDetail: Phase5Sale | null;
  investors: Phase5Investor[]; investorFilterId: string; branches: Array<BranchSummary | BranchListItem>; companyAccountant: boolean;
}): FormCommand {
  const amount = values.amount || '0.00';
  const investorFund = values.investor_fund_amount || '0.00';
  const runningCapital = (total: string, fund: string) => {
    const remaining = moneyCents(total) - moneyCents(fund);
    if (remaining < 0n) throw new Error('Investor Fund allocation cannot exceed the total cost.');
    return moneyFromCents(remaining);
  };
  switch (action.kind) {
    case 'vehicle': return { module: 'vehicle-management', suffix: 'vehicles/', body: { registration: values.registration, model: values.model, branch_id: values.branch_id } };
    case 'purchase': {
      if (!context.selectedVehicle || context.selectedVehicle.id !== action.targetId) throw new Error('Reload the Vehicle before recording its Purchase.');
      const fundUsed = moneyCents(investorFund) > 0n;
      const payment = values.initial_payment_amount || '0.00';
      return { module: 'vehicle-management', suffix: 'purchases/', body: {
        vehicle_id: context.selectedVehicle.id, branch_id: context.selectedVehicle.branch_id,
        purchase_cost: values.purchase_cost, seller_name: values.seller_name, seller_phone: values.seller_phone ?? '',
        investor_id: fundUsed ? values.investor_id : null, investor_fund_amount: investorFund,
        running_capital_amount: runningCapital(values.purchase_cost, investorFund),
        purchased_at: values.purchased_at ? toIso(values.purchased_at) : undefined,
        initial_payment_amount: payment,
        initial_payment_account_id: moneyCents(payment) > 0n ? values.account_id : null,
      } };
    }
    case 'purchasePayment': return { module: 'vehicle-management', suffix: `purchases/${action.targetId}/installments/`, body: { account_id: values.account_id, amount, reference: values.reference ?? '', effective_at: toIso(values.effective_at) } };
    case 'purchaseRefund': return { module: 'vehicle-management', suffix: `purchases/${action.targetId}/refunds/`, body: { account_id: values.account_id, amount, effective_at: toIso(values.effective_at) } };
    case 'purchaseCorrection': return { module: 'vehicle-management', suffix: `purchases/${action.targetId}/corrections/`, body: { purchase_cost: values.purchase_cost, reason: values.reason } };
    case 'expense': {
      if (!context.selectedVehicle || context.selectedVehicle.id !== action.targetId) throw new Error('Reload the Vehicle before adding an expense.');
      return { module: 'vehicle-management', suffix: `vehicles/${context.selectedVehicle.id}/expenses/`, body: {
        amount, description: values.description, investor_id: values.investor_id || null,
        effective_at: toIso(values.effective_at),
      } };
    }
    case 'expensePayment': return { module: 'vehicle-management', suffix: `expenses/${action.targetId}/installments/`, body: { account_id: values.account_id, amount, reference: values.reference, effective_at: toIso(values.effective_at) } };
    case 'expenseRefund': {
      const expense = context.expenses.find((row) => row.id === action.targetId);
      const hasExcess = Boolean(expense && moneyCents(amount) > moneyCents(expense.net_paid));
      const destinationFields = hasExcess
        ? {
            excess_income_category_id: values.excess_income_category_id,
            excess_income_description: values.excess_income_description,
          }
        : {};
      return { module: 'vehicle-management', suffix: `expenses/${action.targetId}/refunds/`, body: {
        account_id: values.account_id,
        amount,
        ...destinationFields,
        effective_at: toIso(values.effective_at),
      } };
    }
    case 'expenseCorrection': return { module: 'vehicle-management', suffix: `expenses/${action.targetId}/corrections/`, body: { amount, reason: values.reason } };
    case 'sale': {
      if (!context.selectedVehicle || context.selectedVehicle.id !== action.targetId) throw new Error('Reload the Vehicle before confirming its Sale.');
      return { module: 'vehicle-management', suffix: 'sales/', body: { vehicle_id: context.selectedVehicle.id, branch_id: context.selectedVehicle.branch_id, sale_price: values.sale_price, buyer_name: values.buyer_name, buyer_phone: values.buyer_phone, sold_at: values.sold_at ? toIso(values.sold_at) : undefined } };
    }
    case 'saleReceipt': return { module: 'vehicle-management', suffix: `sales/${action.targetId}/receipts/`, body: { account_id: values.account_id, amount, reference: values.reference, effective_at: toIso(values.effective_at) } };
    case 'saleRefund': return { module: 'vehicle-management', suffix: `sales/${action.targetId}/refunds/`, body: { account_id: values.account_id, amount, effective_at: toIso(values.effective_at) } };
    case 'saleCorrection': return { module: 'vehicle-management', suffix: `sales/${action.targetId}/corrections/`, body: { sale_price: values.sale_price, reason: values.reason } };
    case 'investor': return { module: 'investment', suffix: 'investors/', body: { name: values.name } };
    case 'investorEdit': return { module: 'investment', suffix: `investors/${action.targetId}/`, body: { name: values.name }, method: 'PATCH' };
    case 'fundCredit': return { module: 'investment', suffix: 'fund/credits/', body: { investor_id: values.investor_id, branch_id: values.branch_id, account_id: values.account_id, amount, reference: values.reference, effective_at: toIso(values.effective_at) } };
    case 'fundCreditCorrection': return { module: 'investment', suffix: `fund/credits/${action.targetId}/corrections/`, body: { to_investor_id: values.to_investor_id, reason: values.reason } };
    case 'principalReturn': return { module: 'investment', suffix: 'fund/principal-returns/', body: { investor_id: values.investor_id, branch_id: values.branch_id, account_id: values.account_id, amount, reference: values.reference, effective_at: toIso(values.effective_at) } };
    case 'vehicleMove': return { module: 'vehicle-management', suffix: `vehicles/${action.targetId}/branch-movements/`, body: { to_branch_id: values.to_branch_id, reason: values.reason } };
    default: throw new Error('Unknown Phase 5 action.');
  }
}

function Notice({ children, tone = 'info' }: { children: React.ReactNode; tone?: 'info' | 'error' | 'success' }) {
  const colors = tone === 'error' ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300' : tone === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-300' : 'border-blue-100 bg-blue-50/70 text-blue-800 dark:border-blue-900 dark:bg-blue-950/20 dark:text-blue-200';
  return <div role={tone === 'error' ? 'alert' : 'status'} className={`rounded-xl border px-3 py-2 text-xs ${colors}`}>{children}</div>;
}

function BranchFilter({ branches, value, onChange }: { branches: Array<BranchSummary | BranchListItem>; value: string; onChange: (value: string) => void }) {
  if (branches.length <= 1) return null;
  return (
    <label className="flex items-center gap-2 text-[11px] font-bold text-gray-500">
      Branch
      <select value={value} onChange={(event) => onChange(event.target.value)} className="h-9 rounded-lg border border-[#e2d8ce] bg-white px-2 text-xs font-semibold text-gray-800 dark:border-zinc-700 dark:bg-zinc-900 dark:text-white">
        <option value="">All authorized Branches</option>
        {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
      </select>
    </label>
  );
}

function FundPanel(props: {
  summary?: Phase5FundSummary; credits: Phase5FundCredit[]; returns: Phase5PrincipalReturn[]; investors: Phase5Investor[]; branches: Array<BranchSummary | BranchListItem>;
  branchId: string; onBranch: (value: string) => void; selectedInvestorId: string; onInvestorFilter: (value: string) => void; onAddInvestor: () => void; onEditInvestor: (investor: Phase5Investor) => void; onCredit: (investorId?: string) => void; onCorrectCredit: (credit: Phase5FundCredit) => void; onReturn: (investorId: string) => void;
  page: number; hasPrevious: boolean; hasNext: boolean; onPage: (page: number) => void; returnPage: number; returnHasPrevious: boolean; returnHasNext: boolean; onReturnPage: (page: number) => void; canProfileWrite: boolean; canFundWrite: boolean; canCreditCorrection: boolean; companyAccountant: boolean;
}) {
  const investorNames = new Map(props.investors.map((row) => [row.id, row.name]));
  const branchNames = new Map(props.branches.map((row) => [row.id, row.name]));
  return (
    <>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <SummaryCard label="Fund credits" value={formatMoney(props.summary?.credit_total)} />
        <SummaryCard label="Principal returned" value={formatMoney(props.summary?.principal_return_total)} />
        <SummaryCard label="Available in your scope" value={formatMoney(props.summary?.available_amount)} />
      </div>
      <div className="rounded-2xl border border-[#eee6de] bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white">Investors</h2>
          <div className="flex flex-wrap gap-2">
            <BranchFilter branches={props.branches} value={props.branchId} onChange={props.onBranch} />
            <select aria-label="Filter by Investor" value={props.selectedInvestorId} onChange={(event) => props.onInvestorFilter(event.target.value)} className="h-9 max-w-[190px] rounded-lg border border-[#e2d8ce] bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950 dark:text-white">
              <option value="">All investors</option>{props.investors.map((investor) => <option key={investor.id} value={investor.id}>{investor.name}</option>)}
            </select>
            <button type="button" disabled={!props.canProfileWrite} onClick={props.onAddInvestor} className="inline-flex h-9 items-center gap-1 rounded-lg bg-[#18181b] px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black"><Plus className="h-3.5 w-3.5" /> Add Investor</button>
            <button type="button" disabled={!props.canFundWrite || !props.investors.length} onClick={() => props.onCredit(props.selectedInvestorId)} className="inline-flex h-9 items-center gap-1 rounded-lg border border-[#e2d8ce] px-3 text-xs font-bold disabled:opacity-50 dark:border-zinc-700"><Plus className="h-3.5 w-3.5" /> Fund Credit</button>
          </div>
        </div>
        {props.investors.length ? <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
          {props.investors.map((investor) => <div key={investor.id} className="flex min-w-0 items-center justify-between gap-2 rounded-xl border border-[#eee6de] p-3 dark:border-zinc-800">
            <div className="min-w-0"><div className="truncate text-xs font-extrabold text-gray-900 dark:text-white">{investor.name}</div><div className="mt-1 text-[10px] text-gray-400">{investor.is_active ? 'Active' : 'Inactive'}</div></div>
             <div className="flex shrink-0 gap-1.5"><button type="button" disabled={!props.canProfileWrite} onClick={() => props.onEditInvestor(investor)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[11px] font-bold disabled:opacity-50 dark:border-zinc-700">Edit</button><button type="button" disabled={!props.canFundWrite} onClick={() => props.onReturn(investor.id)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[11px] font-bold disabled:opacity-50 dark:border-zinc-700">Return principal</button></div>
          </div>)}
        </div> : <Empty>No Investor records are available in this Company.</Empty>}
      </div>
      <div className="rounded-2xl border border-[#eee6de] bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <h2 className="mb-2 text-sm font-extrabold text-gray-900 dark:text-white">Fund credits</h2>
        {props.credits.length ? <div className="flex flex-col divide-y divide-[#eee6de] dark:divide-zinc-800">
          {props.credits.map((credit) => <div key={credit.id} className="grid grid-cols-[1fr_auto] gap-2 py-2.5 text-xs sm:grid-cols-[1.1fr_1fr_auto_1fr]">
            <div className="min-w-0"><div className="truncate font-bold">{investorNames.get(credit.investor_id) ?? 'Investor'}</div><div className="mt-0.5 truncate text-[10px] text-gray-400">{credit.reference}</div>{credit.original_investor_id !== credit.investor_id && <div className="mt-1 text-[10px] text-gray-500">Originally recorded for {investorNames.get(credit.original_investor_id) ?? 'another Investor'}</div>}</div>
            <div className="text-right font-extrabold tabular-nums sm:text-left">{formatMoney(credit.amount)}</div>
            <div className="text-right text-[10px] text-gray-500 sm:text-left">{branchNames.get(credit.branch_id) ?? 'Branch'}</div>
            <div className="col-span-2 text-[10px] text-gray-500 sm:col-span-1 sm:text-right">{displayDate(credit.effective_at)}</div>
            <div className="col-span-2 flex min-w-0 flex-wrap items-center justify-between gap-2 sm:col-span-4">
              <div className="min-w-0 flex-1">
                {credit.attribution_corrections.length > 0 && <div className="truncate text-[10px] text-gray-500">Correction v{credit.correction_version}: {credit.attribution_corrections[credit.attribution_corrections.length - 1]?.reason}</div>}
                {credit.manual_review_required && <div role="status" className="mt-1 rounded-md bg-amber-50 px-2 py-1 text-[10px] leading-4 text-amber-800 dark:bg-amber-950/30 dark:text-amber-200">Linked Vehicle use or principal-return history is unchanged. Accountant review is required; historical Investor calculations are not updated automatically.</div>}
              </div>
              <button type="button" disabled={!props.canCreditCorrection} onClick={() => props.onCorrectCredit(credit)} className="h-8 shrink-0 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Correct Investor</button>
            </div>
          </div>)}
        </div> : <Empty>No Fund credits in this view.</Empty>}
        <PageControls page={props.page} hasPrevious={props.hasPrevious} hasNext={props.hasNext} onChange={props.onPage} />
      </div>
      <div className="rounded-2xl border border-[#eee6de] bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <h2 className="mb-2 text-sm font-extrabold text-gray-900 dark:text-white">Principal returns</h2>
        {props.returns.length ? <div className="flex flex-col divide-y divide-[#eee6de] dark:divide-zinc-800">{props.returns.map((item) => <div key={item.id} className="grid grid-cols-[1fr_auto] gap-2 py-2.5 text-xs sm:grid-cols-[1.1fr_1fr_auto_1fr]"><div className="min-w-0"><div className="truncate font-bold">{investorNames.get(item.investor_id) ?? 'Investor'}</div><div className="mt-0.5 truncate text-[10px] text-gray-400">{item.reference}</div></div><div className="text-right font-extrabold tabular-nums sm:text-left">{formatMoney(item.amount)}</div><div className="text-right text-[10px] text-gray-500 sm:text-left">{branchNames.get(item.branch_id) ?? 'Branch'}</div><div className="col-span-2 text-[10px] text-gray-500 sm:col-span-1 sm:text-right">{displayDate(item.effective_at)}</div></div>)}</div> : <Empty>No principal returns in this view.</Empty>}
        <PageControls page={props.returnPage} hasPrevious={props.returnHasPrevious} hasNext={props.returnHasNext} onChange={props.onReturnPage} />
      </div>
      {!props.companyAccountant && <Notice>Branch view shows only Fund records and available amounts within your authorized Branch scope.</Notice>}
      {!props.canProfileWrite && <Notice tone="info">Investment is OFF. Existing records remain readable; new Investor or Fund changes are disabled.</Notice>}
      {props.canProfileWrite && !props.canFundWrite && <Notice tone="info">Accounting is OFF. Investor profiles remain available, while Fund credits and principal returns are disabled.</Notice>}
    </>
  );
}

function VehiclePanel(props: {
  routeKey: 'Stock / Investor' | 'Running Capital'; vehicles: Phase5Vehicle[]; selectedVehicle: Phase5Vehicle | null; purchase: Phase5Purchase | null; expenses: Phase5Expense[]; sale: Phase5Sale | null;
  branches: Array<BranchSummary | BranchListItem>; branchId: string; search: string; onSearch: (value: string) => void; onBranch: (value: string) => void; onSelectVehicle: (vehicle: Phase5Vehicle) => void;
  onAddVehicle: () => void; onPurchase: (vehicle: Phase5Vehicle) => void; onAddExpense: (vehicle: Phase5Vehicle) => void; onPurchasePayment: (purchase: Phase5Purchase) => void; onPurchaseRefund: (purchase: Phase5Purchase) => void; onPurchaseCorrection: (purchase: Phase5Purchase) => void;
  onExpensePayment: (expense: Phase5Expense) => void; onExpenseRefund: (expense: Phase5Expense) => void; onExpenseCorrection: (expense: Phase5Expense) => void; onSale: (vehicle: Phase5Vehicle) => void; onSaleReceipt: (sale: Phase5Sale) => void; onSaleRefund: (sale: Phase5Sale) => void; onSaleCorrection: (sale: Phase5Sale) => void; onMove: (vehicle: Phase5Vehicle) => void;
  page: number; hasPrevious: boolean; hasNext: boolean; onPage: (page: number) => void; loading: boolean; canVehicleWrite: boolean; canAccountingWrite: boolean; canInvestmentWrite: boolean; companyAccountant: boolean; detailLoading: boolean;
  detailPage: number; detailHasPrevious: boolean; detailHasNext: boolean; onDetailPage: (page: number) => void; expenseRunningCapitalTotal?: string;
}) {
  const runningView = props.routeKey === 'Running Capital';
  return (
    <>
      <div className="flex flex-col gap-2 rounded-2xl border border-[#eee6de] bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:flex-row sm:items-center sm:justify-between sm:p-4">
        <div className="flex flex-1 flex-wrap items-center gap-2">
          <label className="relative min-w-[190px] flex-1 sm:max-w-xs"><span className="sr-only">Search vehicles</span><input value={props.search} onChange={(event) => props.onSearch(event.target.value)} placeholder="Search registration or model" className="h-9 w-full rounded-lg border border-[#e2d8ce] bg-white px-3 text-xs outline-none focus:border-[var(--theme-primary)] dark:border-zinc-700 dark:bg-zinc-950 dark:text-white" /></label>
          <BranchFilter branches={props.branches} value={props.branchId} onChange={props.onBranch} />
        </div>
        {!runningView && <button type="button" disabled={!props.canVehicleWrite} onClick={props.onAddVehicle} className="inline-flex h-9 items-center justify-center gap-1 rounded-lg bg-[#18181b] px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black"><Plus className="h-3.5 w-3.5" /> Register Vehicle</button>}
      </div>
      <div className="rounded-2xl border border-[#eee6de] bg-white p-2 dark:border-zinc-800 dark:bg-zinc-900 sm:p-3">
        {props.loading ? <div role="status" className="p-5 text-center text-xs text-gray-500">Loading vehicle records…</div> : props.vehicles.length ? <div className="flex flex-col gap-1.5">
          {props.vehicles.map((vehicle) => <div key={vehicle.id} className="flex flex-col gap-2 rounded-xl border border-transparent p-2.5 transition hover:border-[#eee6de] hover:bg-gray-50/70 dark:hover:border-zinc-800 dark:hover:bg-zinc-950/50 sm:flex-row sm:items-center sm:justify-between">
            <button type="button" onClick={() => props.onSelectVehicle(vehicle)} className="min-w-0 flex-1 text-left">
              <div className="flex min-w-0 items-center gap-2"><span className="truncate text-xs font-extrabold text-gray-950 dark:text-white">{vehicle.registration}</span><span className="truncate text-xs text-gray-500">{vehicle.model}</span>{vehicle.is_sold && <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[9px] font-bold text-gray-600 dark:bg-zinc-800 dark:text-gray-300">Sold</span>}</div>
              <div className="mt-1 text-[10px] text-gray-400">{vehicle.branch_name} · {vehicle.is_sold ? 'Sale confirmed' : 'Active stock vehicle'}</div>
            </button>
            <div className="flex shrink-0 flex-wrap items-center gap-1.5">
              {!runningView && !vehicle.is_sold && <button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite} onClick={() => props.onSelectVehicle(vehicle)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Open</button>}
              {!runningView && props.companyAccountant && <button type="button" disabled={!props.canVehicleWrite} onClick={() => props.onMove(vehicle)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Move Branch</button>}
            </div>
          </div>)}
        </div> : <Empty>No backend vehicle records match this view.</Empty>}
        <PageControls page={props.page} hasPrevious={props.hasPrevious} hasNext={props.hasNext} onChange={props.onPage} />
      </div>

      {props.selectedVehicle && (
        <div className="rounded-2xl border border-[#e2d8ce] bg-white p-3 dark:border-zinc-700 dark:bg-zinc-900 sm:p-4">
          <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
            <div><div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">Vehicle workspace</div><h2 className="mt-0.5 text-sm font-extrabold text-gray-950 dark:text-white">{props.selectedVehicle.model} · {props.selectedVehicle.registration}</h2><p className="mt-1 text-[10px] text-gray-500">{props.selectedVehicle.branch_name} · {props.selectedVehicle.is_sold ? 'Sold' : 'Active'}</p></div>
            <button type="button" onClick={() => props.onSelectVehicle(props.selectedVehicle!)} aria-label="Close vehicle details" className="rounded-full p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800"><X className="h-4 w-4" /></button>
          </div>
          {props.detailLoading ? <div role="status" className="py-5 text-center text-xs text-gray-500">Loading purchase and expense records…</div> : (
            <>
              {props.purchase ? <div className="mb-3 rounded-xl bg-gray-50 p-3 dark:bg-zinc-950">
                <div className="flex flex-wrap items-center justify-between gap-2"><div><div className="text-[10px] font-bold uppercase text-gray-400">Purchase · {props.purchase.seller_name}{props.purchase.no_advance_warning ? ' · No advance paid' : ''}</div><div className="mt-1 text-xs font-extrabold">Cost {formatMoney(props.purchase.purchase_cost)} <span className="font-medium text-gray-500">· Paid {formatMoney(props.purchase.seller_paid)} · Payable {formatMoney(props.purchase.seller_payable)}</span></div><div className="mt-1 text-[10px] text-gray-500">Investor Fund {formatMoney(props.purchase.investor_fund_amount)} · Running Capital {formatMoney(props.purchase.running_capital_amount)}</div></div>
                  <div className="flex flex-wrap gap-1.5"><button type="button" disabled={!props.canAccountingWrite || moneyCents(props.purchase.seller_payable) <= 0n} onClick={() => props.onPurchasePayment(props.purchase!)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Pay</button><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || moneyCents(props.purchase.seller_paid) <= 0n} onClick={() => props.onPurchaseRefund(props.purchase!)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Refund</button><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || !props.canInvestmentWrite} onClick={() => props.onPurchaseCorrection(props.purchase!)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Correct cost</button></div>
                </div>
              </div> : !props.selectedVehicle.is_sold && <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-gray-50 p-3 dark:bg-zinc-950"><div className="text-xs font-bold">No purchase record yet.</div><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite} onClick={() => props.onPurchase(props.selectedVehicle!)} className="h-8 rounded-lg bg-[#18181b] px-3 text-[10px] font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">Record Purchase</button></div>}

              <div className="mb-2 flex flex-wrap items-center justify-between gap-2"><h3 className="text-xs font-extrabold text-gray-900 dark:text-white">Direct vehicle expenses</h3><button type="button" disabled={!props.canVehicleWrite} onClick={() => props.onAddExpense(props.selectedVehicle!)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700"><Plus className="mr-1 inline h-3 w-3" />Add expense</button></div>
              {props.expenses.length ? <div className="flex flex-col divide-y divide-[#eee6de] dark:divide-zinc-800">{props.expenses.map((expense) => <div key={expense.id} className="flex flex-col gap-2 py-2.5 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><div className="truncate text-xs font-bold">{expense.description} · {formatMoney(expense.amount)}</div><div className="mt-0.5 text-[10px] text-gray-500">Paid {formatMoney(expense.paid_total)} · Payable {formatMoney(expense.payable)} · Investor {formatMoney(expense.investor_fund_amount)} · Running Capital {formatMoney(expense.running_capital_amount)}</div></div><div className="flex flex-wrap gap-1.5"><button type="button" disabled={!props.canAccountingWrite || moneyCents(expense.payable) <= 0n} onClick={() => props.onExpensePayment(expense)} className="h-8 rounded-lg border border-[#e2d8ce] px-2 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Pay</button><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || !props.canInvestmentWrite} onClick={() => props.onExpenseRefund(expense)} className="h-8 rounded-lg border border-[#e2d8ce] px-2 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Refund</button><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || !props.canInvestmentWrite} onClick={() => props.onExpenseCorrection(expense)} className="h-8 rounded-lg border border-[#e2d8ce] px-2 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Correct</button></div></div>)}</div> : <Empty>No direct vehicle expenses recorded.</Empty>}
              <PageControls page={props.detailPage} hasPrevious={props.detailHasPrevious} hasNext={props.detailHasNext} onChange={props.onDetailPage} />

              {props.routeKey === 'Running Capital' && !props.detailLoading && props.expenseRunningCapitalTotal !== undefined && <div className="mt-3 rounded-xl border border-dashed border-[#e2d8ce] p-3 text-[11px] text-gray-600 dark:border-zinc-700 dark:text-gray-300"><strong>Vehicle Company Running Capital:</strong> {formatMoney(moneyFromCents(moneyCents(props.purchase?.running_capital_amount ?? '0.00') + moneyCents(props.expenseRunningCapitalTotal)))}. This includes expenses visible under the selected Branch filter.</div>}

              {props.sale && <div className="mt-3 rounded-xl border border-[#eee6de] p-3 dark:border-zinc-800"><div className="flex flex-wrap items-center justify-between gap-2"><div><div className="text-[10px] font-bold uppercase text-gray-400">Confirmed Sale · {props.sale.buyer_name}</div><div className="mt-1 text-xs font-extrabold">Sale {formatMoney(props.sale.sale_price)} · Received {formatMoney(props.sale.net_received)} · Receivable {formatMoney(props.sale.receivable)}</div><div className="mt-1 text-[10px] text-gray-500">Buyer refund payable {formatMoney(props.sale.refund_payable)} · Buyer {props.sale.buyer_phone}</div></div><div className="flex flex-wrap gap-1.5"><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || (Boolean(props.sale.investor_funded) && !props.canInvestmentWrite) || moneyCents(props.sale.receivable) <= 0n} onClick={() => props.onSaleReceipt(props.sale!)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Receipt</button><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || moneyCents(props.sale.refund_payable) <= 0n} onClick={() => props.onSaleRefund(props.sale!)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Refund</button><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite} onClick={() => props.onSaleCorrection(props.sale!)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Correct Sale</button></div></div><SaleCorrectionHistory corrections={props.sale.corrections} /></div>}
              {!props.selectedVehicle.is_sold && props.purchase && !runningView && <button type="button" disabled={!props.canVehicleWrite} onClick={() => props.onSale(props.selectedVehicle!)} className="mt-3 h-9 rounded-lg bg-[#18181b] px-3.5 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">Confirm Sale</button>}
            </>
          )}
        </div>
      )}
      {!props.canVehicleWrite && <Notice>Vehicle Management is OFF. Existing backend records are read-only, except permitted pre-existing payables when Accounting is ON.</Notice>}
    </>
  );
}

function SalesPanel(props: {
  routeKey: RouteKey; sales: Phase5Sale[]; branches: Array<BranchSummary | BranchListItem>; branchId: string; onBranch: (value: string) => void;
  onReceipt: (sale: Phase5Sale) => void; onRefund: (sale: Phase5Sale) => void; onCorrection: (sale: Phase5Sale) => void; page: number; hasPrevious: boolean; hasNext: boolean; onPage: (page: number) => void; canRead: boolean; canVehicleWrite: boolean; canAccountingWrite: boolean; canInvestmentWrite: boolean;
}) {
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-[#eee6de] bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <BranchFilter branches={props.branches} value={props.branchId} onChange={props.onBranch} />
        <span className="text-[10px] text-gray-500">{props.sales.length} sale records on this page</span>
      </div>
      <div className="rounded-2xl border border-[#eee6de] bg-white p-2 dark:border-zinc-800 dark:bg-zinc-900 sm:p-3">
        {props.sales.length ? <div className="flex flex-col gap-1.5">{props.sales.map((sale) => <div key={sale.id} className="rounded-xl border border-transparent p-2.5 hover:border-[#eee6de] dark:hover:border-zinc-800"><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><div className="truncate text-xs font-extrabold">{sale.vehicle_registration} · {sale.vehicle_model}</div><div className="mt-1 truncate text-[10px] text-gray-500">{sale.buyer_name} · {sale.buyer_phone} · {sale.branch_name} · {displayDate(sale.sold_at)}</div><div className="mt-1 text-xs font-bold">Sale {formatMoney(sale.sale_price)} · Received {formatMoney(sale.net_received)} · Due {formatMoney(sale.receivable)} · Refund payable {formatMoney(sale.refund_payable)}</div></div><div className="flex shrink-0 flex-wrap gap-1.5">{props.routeKey === 'Collections' && <button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || (Boolean(sale.investor_funded) && !props.canInvestmentWrite) || moneyCents(sale.receivable) <= 0n} onClick={() => props.onReceipt(sale)} className="h-8 rounded-lg bg-[#18181b] px-2.5 text-[10px] font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">Add Receipt</button>}{props.routeKey === 'Sale Corrections & Refunds' && <><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite || moneyCents(sale.refund_payable) <= 0n} onClick={() => props.onRefund(sale)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Buyer Refund</button><button type="button" disabled={!props.canVehicleWrite || !props.canAccountingWrite} onClick={() => props.onCorrection(sale)} className="h-8 rounded-lg border border-[#e2d8ce] px-2.5 text-[10px] font-bold disabled:opacity-50 dark:border-zinc-700">Correct Price</button></>}</div></div><SaleCorrectionHistory corrections={sale.corrections} /></div>)}</div> : <Empty>No confirmed Sale records are available in this view.</Empty>}
        <PageControls page={props.page} hasPrevious={props.hasPrevious} hasNext={props.hasNext} onChange={props.onPage} />
      </div>
      {!props.canVehicleWrite && <Notice>Vehicle Management is OFF. New sales, receipts, refunds and corrections are disabled according to the current module gates.</Notice>}
      {!props.canAccountingWrite && <Notice>Accounting is OFF. Actual receipts and refunds cannot be posted.</Notice>}
      {props.canVehicleWrite && props.canAccountingWrite && !props.canInvestmentWrite && props.sales.some((sale) => Boolean(sale.investor_funded)) && <Notice>Investment is OFF. Receipts for Investor-funded Vehicles are paused; Sale corrections and buyer refunds remain available. Phase 5 does not refresh Investor Profit calculations or post Investor settlements; have an Accountant review affected records manually.</Notice>}
    </>
  );
}

function SaleCorrectionHistory({ corrections }: { corrections: Phase5SaleCorrection[] }) {
  if (!corrections.length) return null;
  return (
    <details className="mt-2 rounded-lg border border-[#eee6de] bg-gray-50 px-2.5 py-2 dark:border-zinc-800 dark:bg-zinc-950">
      <summary className="cursor-pointer text-[10px] font-bold text-gray-600 dark:text-gray-300">Price correction history ({corrections.length})</summary>
      <ol className="mt-2 flex flex-col gap-2">
        {corrections.map((correction) => (
          <li key={correction.id} className="border-t border-[#eee6de] pt-2 first:border-0 first:pt-0 dark:border-zinc-800">
            <div className="text-[10px] font-bold">v{correction.version} · {formatMoney(correction.previous_sale_price)} → {formatMoney(correction.sale_price)}</div>
            <p className="mt-0.5 text-[10px] text-gray-700 dark:text-gray-300">{correction.reason}</p>
            <p className="mt-0.5 text-[9px] text-gray-500">Effective {displayDateTime(correction.effective_at)} · Recorded {displayDateTime(correction.recorded_at)}</p>
          </li>
        ))}
      </ol>
    </details>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return <div className="rounded-2xl border border-[#eee6de] bg-white px-3.5 py-3 dark:border-zinc-800 dark:bg-zinc-900"><div className="text-[10px] font-bold uppercase tracking-wide text-gray-400">{label}</div><div className="mt-1 text-lg font-extrabold tabular-nums text-gray-950 dark:text-white">{value}</div></div>;
}

function Empty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl bg-gray-50 px-3 py-6 text-center text-xs font-medium text-gray-500 dark:bg-zinc-950 dark:text-gray-400">{children}</div>;
}
