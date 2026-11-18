import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Building2, Check, ChevronLeft, ChevronRight, FileText, Plus, Settings2, X } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { useCompanyModuleStates } from '../../api/queries';
import {
  accountingCorrectionPath,
  accountingMutation,
  AccountingEventDetail,
  AccountingEventRow,
  AccountingEventType,
} from '../../api/accountingApi';
import {
  useAccountingAccounts,
  useAccountingBranches,
  useAccountingCategories,
  useAccountingEvent,
  useAccountingEvents,
  useAccountingResult,
} from '../../api/accountingQueries';
import { queryKeys } from '../../api/queryKeys';

type Action = 'INCOME' | 'EXPENSE' | 'RECEIPT' | 'PAYMENT' | 'OPENING_BALANCE' | 'TRANSFER' | 'CORRECTION' | 'REALLOCATION' | 'ACCOUNT' | 'CATEGORY';
type DialogState = { mode: 'tools' } | { mode: 'form'; action: Action; eventId?: string; applicationId?: string };
type AccountingModuleState = 'unconfigured' | 'enabled' | 'disabled' | 'unknown';

export function resolveFormTargetEventId(
  action: Action | undefined,
  values: Readonly<Record<string, string>>,
): string {
  return action === 'REALLOCATION'
    ? values.new_target_event_id ?? ''
    : values.target_event_id ?? '';
}

export function resolveReallocationSourceEventId(
  selectedEventId: string | null,
  application: { source_event_id: string } | undefined,
): string | null {
  if (!application || application.source_event_id === selectedEventId) return null;
  return application.source_event_id;
}

const inputClass = 'w-full rounded-xl border border-[#e2d8ce] bg-white px-3 py-2 text-xs font-semibold text-gray-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white';
const labelClass = 'mb-1 block text-xs font-bold text-gray-700 dark:text-gray-300';

function localDateTime(value = new Date()): string {
  const offset = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 16);
}

function displayDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

function formatINR(value: string | undefined): string {
  const amount = Number(value ?? '0');
  return `₹${new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 }).format(Number.isFinite(amount) ? amount : 0)}`;
}

function eventIsCurrent(event: AccountingEventDetail): boolean {
  return event.effect_sign === 1 && event.reversal_event_ids.length === 0 && event.replacement_event_ids.length === 0;
}

function activeApplications(event: AccountingEventDetail) {
  const reversed = new Set(event.applications.filter((row) => row.effect_sign === -1 && row.reversal_of_id).map((row) => row.reversal_of_id));
  return event.applications.filter((row) => row.effect_sign === 1 && !reversed.has(row.id));
}

function ModalFrame({ title, children, onClose }: React.PropsWithChildren<{ title: string; onClose: () => void }>) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section role="dialog" aria-modal="true" aria-label={title} className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-[24px] border border-[#e2d8ce] bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex items-center justify-between border-b border-[#f0e7df] px-5 py-4 dark:border-zinc-800">
          <div>
            <h2 className="text-base font-extrabold text-gray-950 dark:text-white">{title}</h2>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">Company Accounting · Backend records</p>
          </div>
          <button type="button" aria-label="Close" onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800"><X className="h-4 w-4" /></button>
        </div>
        {children}
      </section>
    </div>
  );
}

export const CompanyAccountingView: React.FC<{
  routeKey: string;
  onSuccess?: (message: string) => void;
}> = ({ routeKey, onSuccess }) => {
  const { user, currentCompany } = useAuth();
  const queryClient = useQueryClient();
  const moduleStatesQuery = useCompanyModuleStates();
  const branchesQuery = useAccountingBranches();
  const accountsQuery = useAccountingAccounts();
  const categoriesQuery = useAccountingCategories();
  const companyId = currentCompany?.id ?? '';
  const userId = user?.id ?? '';
  const roles = currentCompany?.roles ?? [];
  const companyWideRoles = currentCompany?.company_wide_roles ?? [];
  const canAccount = roles.includes('accountant');
  const isCompanyAccountant = companyWideRoles.includes('accountant');
  const moduleState = (moduleStatesQuery.data?.modules.find((row) => row.code === 'accounting')?.state ?? 'unknown') as AccountingModuleState;
  const writeStateKnown = moduleStatesQuery.isSuccess && moduleState !== 'unknown';
  const [selectedBranch, setSelectedBranch] = useState('all');
  const [eventPage, setEventPage] = useState(1);
  const eventType: AccountingEventType | undefined = routeKey === 'Company Income' ? 'INCOME'
    : routeKey === 'Company Expenses' ? 'EXPENSE'
      : undefined;
  const [period, setPeriod] = useState<'monthly' | 'h1' | 'h2' | 'annual'>('annual');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [toolsEventType, setToolsEventType] = useState<AccountingEventType | undefined>();
  const [toolsPage, setToolsPage] = useState(1);
  const [targetPage, setTargetPage] = useState(1);

  useEffect(() => {
    setEventPage(1);
    setSelectedEventId(null);
  }, [routeKey]);

  const branches = branchesQuery.data ?? [];
  const accounts = accountsQuery.data ?? [];
  const categories = categoriesQuery.data ?? [];
  const activeAccounts = accounts.filter((account) => account.is_active);
  const activeCategories = categories.filter((category) => category.is_active);
  const branchId = selectedBranch === 'all' ? undefined : selectedBranch;
  const reportBranchId = isCompanyAccountant
    ? branchId
    : branchId ?? (branches.length === 1 ? branches[0].id : undefined);
  const reportReady = isCompanyAccountant || Boolean(reportBranchId);

  const eventQuery = useAccountingEvents({ page: eventPage, eventType, branchId });
  const reportQuery = useAccountingResult({ period, year, month: period === 'monthly' ? month : undefined, branchId: reportBranchId, enabled: routeKey === 'Accounting' });
  const selectedEventQuery = useAccountingEvent(selectedEventId);
  const eventDetail = selectedEventQuery.data;
  const selectedApplication = dialog?.mode === 'form' && dialog.action === 'REALLOCATION' && eventDetail
    ? activeApplications(eventDetail).find((application) => application.id === dialog.applicationId)
    : undefined;
  const reallocationSourceEventId = resolveReallocationSourceEventId(eventDetail?.id ?? null, selectedApplication);
  const reallocationSourceQuery = useAccountingEvent(reallocationSourceEventId);
  const reallocationSourceEvent = selectedApplication
    ? selectedApplication.source_event_id === eventDetail?.id
      ? eventDetail
      : reallocationSourceQuery.data
    : undefined;

  const targetType: AccountingEventType | undefined = dialog?.mode === 'form'
    ? dialog.action === 'RECEIPT' ? 'INCOME'
      : dialog.action === 'PAYMENT' ? 'EXPENSE'
        : dialog.action === 'REALLOCATION' && reallocationSourceEvent?.event_type === 'RECEIPT' ? 'INCOME'
          : dialog.action === 'REALLOCATION' && reallocationSourceEvent?.event_type === 'PAYMENT' ? 'EXPENSE'
            : undefined
    : undefined;
  const targetQuery = useAccountingEvents({
    page: targetPage,
    eventType: targetType,
    branchId,
    enabled: Boolean(targetType && dialog?.mode === 'form'),
  });
  const formTargetId = resolveFormTargetEventId(
    dialog?.mode === 'form' ? dialog.action : undefined,
    form,
  );
  const formTargetQuery = useAccountingEvent(formTargetId || null);
  const toolsEventsQuery = useAccountingEvents({
    page: toolsPage,
    eventType: toolsEventType,
    branchId,
    enabled: dialog?.mode === 'tools',
  });

  const title = routeKey === 'Company Income' ? 'Company Income'
    : routeKey === 'Company Expenses' ? 'Company Expenses'
      : routeKey === 'Audit & Corrections' ? 'Accounting Audit & Corrections'
        : routeKey === 'Transactions' ? 'Accounting Transactions'
          : 'Company Accounting';
  const subtitle = routeKey === 'Company Income'
    ? 'Recognized Company Income and separate actual Receipts'
    : routeKey === 'Company Expenses'
      ? 'Recognized Company Expenses and separate actual Payments'
      : 'Company-scoped Income, Expense, cash movements and immutable correction history';

  const filteredEvents = useMemo(() => eventQuery.data?.results ?? [], [eventQuery.data]);
  const currentReallocationTargetId = selectedApplication?.target_event_id;
  const availableTargetEvents = (targetQuery.data?.results ?? []).filter((row) =>
    row.effect_sign === 1 && !(dialog?.mode === 'form' && dialog.action === 'REALLOCATION' && row.id === currentReallocationTargetId)
  );

  function update(field: string, value: string) {
    setForm((previous) => ({ ...previous, [field]: value }));
    setError(null);
  }

  function defaultBranch() {
    if (selectedBranch !== 'all') return selectedBranch;
    if (!isCompanyAccountant && branches.length === 1) return branches[0].id;
    return '';
  }

  function openForm(action: Action, options: { event?: AccountingEventDetail; applicationId?: string } = {}) {
    setTargetPage(1);
    const event = options.event;
    const next: Record<string, string> = {
      amount: '',
      description: event?.description ?? '',
      source_reference: event?.source_reference ?? '',
      kind: '',
      label: '',
      account_type: '',
      branch_id: event?.branch_id ?? defaultBranch(),
      effective_at: localDateTime(),
      reason: '',
      outcome: '',
      event_occurred: '',
      account_id: event?.account_id ?? activeAccounts[0]?.id ?? '',
      category_id: event?.category_id ?? activeCategories.find((category) => category.is_active)?.id ?? '',
      target_event_id: '',
      new_target_event_id: '',
      from_account_id: event?.from_account_id ?? activeAccounts[0]?.id ?? '',
      to_account_id: event?.to_account_id ?? activeAccounts.find((account) => account.id !== (event?.from_account_id ?? activeAccounts[0]?.id))?.id ?? '',
    };
    if (event) next.amount = event.amount;
    if (event?.event_type === 'OPENING_BALANCE') {
      next.amount = event.movements[0]?.delta ?? '';
      next.description = event.description;
    }
    if (event?.event_type === 'TRANSFER') {
      next.amount = event.amount;
      next.description = event.description;
    }
    if (action === 'REALLOCATION' && options.applicationId) next.new_target_event_id = '';
    setForm(next);
    setTargetPage(1);
    setError(null);
    setDialog({ mode: 'form', action, eventId: event?.id, applicationId: options.applicationId });
  }

  async function saveForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user || !currentCompany || !dialog || dialog.mode !== 'form') return;
    setError(null);
    setSubmitting(true);
    try {
      const selectedBranchValue = form.branch_id || null;
      const dateValue = form.effective_at ? new Date(form.effective_at).toISOString() : undefined;
      let path = '';
      let method: 'POST' | 'PATCH' = 'POST';
      let body: Record<string, unknown> = {};
      switch (dialog.action) {
        case 'INCOME':
        case 'EXPENSE':
          path = dialog.action === 'INCOME' ? 'incomes/' : 'expenses/';
          body = {
            amount: form.amount,
            branch_id: selectedBranchValue,
            category_id: form.category_id,
            description: form.description.trim(),
            source_reference: form.source_reference.trim(),
            effective_at: dateValue,
          };
          break;
        case 'RECEIPT':
        case 'PAYMENT':
          if (!formTargetQuery.data?.outstanding_amount) {
            throw new Error('Choose a current Income or Expense with an outstanding balance.');
          }
          path = dialog.action === 'RECEIPT' ? 'receipts/' : 'payments/';
          body = {
            amount: form.amount,
            branch_id: selectedBranchValue,
            account_id: form.account_id,
            target_event_id: form.target_event_id,
            effective_at: dateValue,
            description: form.description.trim(),
            source_reference: form.source_reference.trim(),
          };
          break;
        case 'OPENING_BALANCE':
          path = 'opening-balances/';
          body = {
            account_id: form.account_id,
            branch_id: selectedBranchValue,
            amount: form.amount,
            effective_at: dateValue,
            reason: form.reason.trim(),
            source_reference: form.source_reference.trim(),
          };
          break;
        case 'TRANSFER':
          path = 'transfers/';
          body = {
            branch_id: selectedBranchValue,
            from_account_id: form.from_account_id,
            to_account_id: form.to_account_id,
            amount: form.amount,
            effective_at: dateValue,
            reason: form.reason.trim(),
            source_reference: form.source_reference.trim(),
          };
          break;
        case 'ACCOUNT':
          path = 'accounts/';
          body = { account_type: form.account_type, label: form.label.trim() };
          break;
        case 'CATEGORY':
          path = 'categories/';
          body = { kind: form.kind, label: form.label.trim() };
          break;
        case 'CORRECTION': {
          if (!dialog.eventId) throw new Error('Select an Accounting record to correct.');
          const target = selectedEventQuery.data;
          if (!target) throw new Error('The Accounting record detail is still loading.');
          if (form.outcome !== 'REVERSE_ONLY' && form.outcome !== 'REVERSE_AND_REPLACE') {
            throw new Error('Choose a correction outcome.');
          }
          if (form.outcome === 'REVERSE_ONLY' && form.event_occurred !== 'false') {
            throw new Error('Reverse only is for a false or duplicate entry. Choose “No” for whether the event happened.');
          }
          if (form.outcome === 'REVERSE_AND_REPLACE' && form.event_occurred !== 'true') {
            throw new Error('A replacement is for a real event with incorrect details. Choose “Yes” for whether it happened.');
          }
          const replacement: Record<string, unknown> = {};
          if (form.outcome === 'REVERSE_AND_REPLACE') {
            if (target.event_type === 'INCOME' || target.event_type === 'EXPENSE') {
              replacement.amount = form.amount;
              replacement.branch_id = selectedBranchValue;
              replacement.category_id = form.category_id;
              replacement.description = form.description.trim();
              replacement.source_reference = form.source_reference.trim();
            } else if (target.event_type === 'RECEIPT' || target.event_type === 'PAYMENT') {
              replacement.amount = form.amount;
              replacement.branch_id = selectedBranchValue;
              replacement.account_id = form.account_id;
              replacement.effective_at = dateValue;
              replacement.description = form.description.trim();
              replacement.source_reference = form.source_reference.trim();
            } else if (target.event_type === 'OPENING_BALANCE') {
              replacement.amount = form.amount;
              replacement.description = form.description.trim();
              replacement.source_reference = form.source_reference.trim();
            } else {
              replacement.branch_id = selectedBranchValue;
              replacement.from_account_id = form.from_account_id;
              replacement.to_account_id = form.to_account_id;
              replacement.amount = form.amount;
              replacement.effective_at = dateValue;
              replacement.description = form.description.trim();
              replacement.source_reference = form.source_reference.trim();
            }
          }
          const outcome = form.outcome;
          path = accountingCorrectionPath(target.event_type, dialog.eventId, outcome);
          const correction = {
            outcome: form.outcome,
            event_occurred: form.event_occurred === 'true',
            reason: form.reason.trim(),
            ...(form.outcome === 'REVERSE_AND_REPLACE' ? { replacement } : {}),
          };
          if (target.event_type === 'INCOME' || target.event_type === 'EXPENSE') {
            body = correction;
          } else if (target.event_type === 'RECEIPT') {
            body = correction;
          } else if (target.event_type === 'PAYMENT') {
            body = correction;
          } else if (target.event_type === 'OPENING_BALANCE') {
            body = {
              outcome,
              event_occurred: form.event_occurred === 'true',
              reason: form.reason.trim(),
              replacement_amount: outcome === 'REVERSE_ONLY' ? '0.00' : form.amount,
              source_reference: form.source_reference.trim(),
            };
          } else if (outcome === 'REVERSE_ONLY') {
            body = {
              outcome,
              event_occurred: form.event_occurred === 'true',
              reason: form.reason.trim(),
            };
          } else {
            body = correction;
          }
          break;
        }
        case 'REALLOCATION':
          if (!dialog.applicationId) throw new Error('Select an active application to reallocate.');
          if (!formTargetQuery.data?.outstanding_amount) {
            throw new Error('Choose a current Income or Expense with an outstanding balance.');
          }
          path = `applications/${encodeURIComponent(dialog.applicationId)}/reallocations/`;
          body = { target_event_id: form.new_target_event_id, reason: form.reason.trim() };
          break;
      }
      if (!path) throw new Error('Unsupported Accounting action.');
      await accountingMutation(companyId, userId, path, method, body);
      await queryClient.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) });
      setDialog(null);
      setSelectedEventId(null);
      onSuccess?.('Accounting record saved.');
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : 'The Accounting request failed.');
    } finally {
      setSubmitting(false);
    }
  }

  function handleRowSelect(row: AccountingEventRow) {
    setSelectedEventId(row.id);
    setError(null);
  }

  function renderSelect(name: string, label: string, value: string, options: Array<{ id: string; label: string }>, required = true) {
    return (
      <div>
        <label className={labelClass} htmlFor={`accounting-${name}`}>{label}</label>
        <select id={`accounting-${name}`} className={inputClass} value={value} required={required} onChange={(event) => update(name, event.target.value)}>
          <option value="">Select…</option>
          {options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </select>
      </div>
    );
  }

  function renderInput(name: string, label: string, value: string, type = 'text', options: { required?: boolean; min?: string; step?: string; max?: string } = {}) {
    return (
      <div>
        <label className={labelClass} htmlFor={`accounting-${name}`}>{label}</label>
        <input id={`accounting-${name}`} className={inputClass} type={type} value={value} required={options.required ?? true} min={options.min} max={options.max} step={options.step} onChange={(event) => update(name, event.target.value)} />
      </div>
    );
  }

  const accountsForPage = accounts.filter((account) => isCompanyAccountant || account.is_active);
  const pageLabel = eventQuery.data?.count === 1 ? '1 record' : `${eventQuery.data?.count ?? 0} records`;
  const formTitle: Record<Action, string> = {
    INCOME: 'Record Company Income', EXPENSE: 'Record Company Expense', RECEIPT: 'Record Actual Receipt', PAYMENT: 'Record Actual Payment',
    OPENING_BALANCE: 'Record Opening Balance', TRANSFER: 'Record Account Transfer', CORRECTION: 'Correct Accounting Record',
    REALLOCATION: 'Reallocate Cash Application', ACCOUNT: 'Add Cash / Bank Account', CATEGORY: 'Add Income / Expense Category',
  };

  return (
    <div className="space-y-4 sm:space-y-5 animate-in fade-in duration-150">
      <div className="flex flex-col gap-3 border-b border-[#f2ebe5] pb-2 md:flex-row md:items-center md:justify-between dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">VIRMS ACCOUNTING WORKSPACE</div>
          <h1 className="mt-0.5 text-xl font-extrabold tracking-tight text-gray-950 sm:text-2xl dark:text-white">{title}</h1>
          <p className="mt-0.5 text-xs font-medium text-gray-500 dark:text-gray-400">{subtitle}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-full border border-[#e2d8ce] bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-gray-300">
            <Building2 className="h-3.5 w-3.5 text-gray-500" />
            <select aria-label="Accounting Branch filter" value={selectedBranch} onChange={(event) => { setSelectedBranch(event.target.value); setEventPage(1); }} className="cursor-pointer border-none bg-transparent pr-2 font-bold focus:outline-none">
              <option value="all">{isCompanyAccountant ? 'All Company Branches' : 'All Assigned Branches'}</option>
              {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
            </select>
          </div>
          {canAccount && routeKey === 'Company Income' && (
            <button type="button" disabled={!writeStateKnown || moduleState !== 'enabled'} onClick={() => openForm('INCOME')} className="inline-flex items-center gap-1.5 rounded-full bg-[#18181b] px-4 py-2 text-xs font-bold text-white shadow-xs transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-50">
              <Plus className="h-3.5 w-3.5 text-[var(--theme-primary)]" /> Record Income
            </button>
          )}
          {canAccount && routeKey === 'Company Expenses' && (
            <button type="button" disabled={!writeStateKnown || moduleState !== 'enabled'} onClick={() => openForm('EXPENSE')} className="inline-flex items-center gap-1.5 rounded-full bg-[#18181b] px-4 py-2 text-xs font-bold text-white shadow-xs transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-50">
              <Plus className="h-3.5 w-3.5 text-[var(--theme-primary)]" /> Record Expense
            </button>
          )}
          <button type="button" onClick={() => setDialog({ mode: 'tools' })} className="inline-flex items-center gap-1.5 rounded-full border border-[#e2d8ce] bg-white px-3.5 py-2 text-xs font-bold text-gray-800 transition hover:bg-gray-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-gray-100 dark:hover:bg-zinc-700">
            <Settings2 className="h-3.5 w-3.5" /> Accounting tools
          </button>
        </div>
      </div>

      {moduleStatesQuery.isError && (
        <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
          Accounting module status could not be verified. New financial records are disabled until it can be checked.
        </div>
      )}
      {moduleStatesQuery.isSuccess && (moduleState === 'disabled' || moduleState === 'unconfigured') && (
        <div role="status" className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
          {moduleState === 'disabled'
            ? 'Accounting is OFF. New Income, Expense, account, category, opening-balance and transfer records are disabled. The server may still accept eligible settlements or corrections for pre-OFF records.'
            : 'Accounting has not been configured. Records can be reviewed, but mutations are unavailable.'}
        </div>
      )}

      {routeKey === 'Accounting' && (
        <section className="dashboard-card-solid rounded-[24px] p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold text-gray-950 dark:text-white">Recognized Accounting Result</h2>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">Income − Expense · reporting window only · does not close or reset a period</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <select aria-label="Reporting period" className={inputClass + ' w-auto'} value={period} onChange={(event) => setPeriod(event.target.value as typeof period)}>
                <option value="monthly">Monthly</option><option value="h1">H1</option><option value="h2">H2</option><option value="annual">Annual</option>
              </select>
              <input aria-label="Reporting year" className={inputClass + ' w-24'} type="number" min="1900" max="9998" value={year} onChange={(event) => setYear(Number(event.target.value))} />
              {period === 'monthly' && <select aria-label="Reporting month" className={inputClass + ' w-auto'} value={month} onChange={(event) => setMonth(Number(event.target.value))}>{Array.from({ length: 12 }, (_, index) => <option key={index + 1} value={index + 1}>{new Date(2000, index, 1).toLocaleString('en', { month: 'long' })}</option>)}</select>}
            </div>
          </div>
          {!reportReady ? <p role="status" className="text-xs text-amber-700 dark:text-amber-300">Select one assigned Branch to calculate this report.</p> : reportQuery.isPending ? <p className="text-xs text-gray-500">Loading verified Accounting result…</p> : reportQuery.isError ? <p role="alert" className="text-xs text-red-700 dark:text-red-300">{reportQuery.error instanceof Error ? reportQuery.error.message : 'Accounting result could not be loaded.'}</p> : reportQuery.data && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {[
                ['Recognized Income', reportQuery.data.income_amount],
                ['Recognized Expense', reportQuery.data.expense_amount],
                ['Accounting Result', reportQuery.data.accounting_result_amount],
              ].map(([label, value], index) => (
                <div key={label} className={`rounded-[20px] p-4 ${index === 2 ? 'dashboard-card-orange text-white' : 'dashboard-card-solid'}`}>
                  <div className={`text-[11px] font-medium ${index === 2 ? 'text-white/90' : 'text-gray-500 dark:text-gray-400'}`}>{label}</div>
                  <div className={`mt-2 text-xl font-bold ${index === 2 ? 'text-white' : 'text-gray-950 dark:text-white'}`}>{formatINR(value)}</div>
                </div>
              ))}
            </div>
          )}
          <p className="mt-3 text-[10px] text-gray-500 dark:text-gray-400">Source: {reportQuery.data?.timezone ?? 'Asia/Kolkata'} effective-date records. Cash Receipts and Payments remain separate.</p>
        </section>
      )}

      <div className="dashboard-card-solid overflow-hidden rounded-[24px]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#f0e7df] px-5 py-4 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-gray-500" />
            <h2 className="text-xs font-bold text-gray-900 dark:text-white">{eventType ? `${eventType[0]}${eventType.slice(1).toLowerCase()} register` : 'Accounting event register'}</h2>
          </div>
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">{pageLabel} · page {eventPage}</div>
        </div>
        {eventQuery.isPending ? <div role="status" className="p-8 text-center text-xs text-gray-500">Loading Company records…</div>
          : eventQuery.isError ? <div role="alert" className="p-8 text-center text-xs text-red-700 dark:text-red-300">{eventQuery.error instanceof Error ? eventQuery.error.message : 'Accounting records could not be loaded.'}</div>
            : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-xs">
                  <thead><tr className="border-b border-[#f0e7df] bg-gray-50/50 dark:border-zinc-800 dark:bg-zinc-800/30">
                    {['Effective date', 'Branch', 'Record', 'Description / Reference', 'Amount'].map((heading) => <th key={heading} className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-gray-600 dark:text-gray-300">{heading}</th>)}
                  </tr></thead>
                  <tbody className="divide-y divide-[#f5ede5] dark:divide-zinc-800/60">
                    {filteredEvents.length === 0 ? <tr><td colSpan={5} className="py-12 text-center text-xs text-gray-500">No Accounting records in this view.</td></tr> : filteredEvents.map((row) => (
                      <tr key={row.id} className="cursor-pointer hover:bg-gray-50/70 dark:hover:bg-zinc-800/40" onClick={() => handleRowSelect(row)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') handleRowSelect(row); }} tabIndex={0} aria-label={`Open ${row.event_type} record ${row.source_reference}`}>
                        <td className="whitespace-nowrap px-4 py-3 text-gray-600 dark:text-gray-300">{displayDate(row.effective_at)}</td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{row.branch_name ?? 'Company-wide'}</td>
                        <td className="px-4 py-3 font-bold text-gray-900 dark:text-gray-100">{row.event_type.replace('_', ' ')}{row.effect_sign === -1 ? ' · reversal' : ''}</td>
                        <td className="px-4 py-3"><span className="block font-semibold text-gray-900 dark:text-gray-100">{row.description}</span><span className="text-[10px] text-gray-500">{row.source_reference}{row.category_name ? ` · ${row.category_name}` : ''}</span></td>
                        <td className={`whitespace-nowrap px-4 py-3 text-right font-mono font-bold ${row.effect_sign === -1 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'}`}>{row.effect_sign === -1 ? '−' : ''}{formatINR(row.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        <div className="flex items-center justify-end gap-2 border-t border-[#f0e7df] px-4 py-3 dark:border-zinc-800">
          <button type="button" disabled={!eventQuery.data?.previous || eventPage <= 1} onClick={() => setEventPage((value) => Math.max(1, value - 1))} className="inline-flex items-center gap-1 rounded-full border border-[#e2d8ce] px-3 py-1.5 text-xs font-bold disabled:opacity-40 dark:border-zinc-700"><ChevronLeft className="h-3.5 w-3.5" /> Previous</button>
          <button type="button" disabled={!eventQuery.data?.next} onClick={() => setEventPage((value) => value + 1)} className="inline-flex items-center gap-1 rounded-full border border-[#e2d8ce] px-3 py-1.5 text-xs font-bold disabled:opacity-40 dark:border-zinc-700">Next <ChevronRight className="h-3.5 w-3.5" /></button>
        </div>
      </div>

      {dialog?.mode === 'tools' && (
        <ModalFrame title="Accounting tools and event history" onClose={() => { setDialog(null); setSelectedEventId(null); }}>
          <div className="flex flex-wrap gap-2 border-b border-[#f0e7df] px-5 py-3 dark:border-zinc-800">
            {canAccount && moduleState === 'enabled' && <>
              {routeKey !== 'Company Income' && <button type="button" onClick={() => openForm('INCOME')} className="rounded-full bg-[#18181b] px-3 py-1.5 text-[11px] font-bold text-white">Record Income</button>}
              {routeKey !== 'Company Expenses' && <button type="button" onClick={() => openForm('EXPENSE')} className="rounded-full bg-[#18181b] px-3 py-1.5 text-[11px] font-bold text-white">Record Expense</button>}
              {isCompanyAccountant && <>
                <button type="button" onClick={() => openForm('OPENING_BALANCE')} className="rounded-full border border-[#e2d8ce] px-3 py-1.5 text-[11px] font-bold dark:border-zinc-700">Opening balance</button>
                <button type="button" onClick={() => openForm('TRANSFER')} className="rounded-full border border-[#e2d8ce] px-3 py-1.5 text-[11px] font-bold dark:border-zinc-700">Transfer</button>
                <button type="button" onClick={() => openForm('ACCOUNT')} className="rounded-full border border-[#e2d8ce] px-3 py-1.5 text-[11px] font-bold dark:border-zinc-700">Add account</button>
                <button type="button" onClick={() => openForm('CATEGORY')} className="rounded-full border border-[#e2d8ce] px-3 py-1.5 text-[11px] font-bold dark:border-zinc-700">Add category</button>
              </>}
            </>}
          </div>
          <div className="grid min-h-0 gap-4 overflow-y-auto p-5 lg:grid-cols-[1fr_0.9fr]">
            <div className="min-w-0">
              <div className="mb-2 flex items-center justify-between gap-2">
                <h3 className="text-xs font-bold text-gray-900 dark:text-white">All Accounting events</h3>
                <select aria-label="Event type filter" className={inputClass + ' w-auto'} value={toolsEventType ?? ''} onChange={(event) => { setToolsEventType((event.target.value || undefined) as AccountingEventType | undefined); setToolsPage(1); setSelectedEventId(null); }}>
                  <option value="">All types</option>{(['INCOME', 'EXPENSE', 'RECEIPT', 'PAYMENT', 'OPENING_BALANCE', 'TRANSFER', 'GARAGE_RECEIPT', 'GARAGE_COST_PAYMENT', 'LABOUR_PAYMENT'] as AccountingEventType[]).map((type) => <option key={type} value={type}>{type.replaceAll('_', ' ')}</option>)}
                </select>
              </div>
              {toolsEventsQuery.isPending ? <p className="py-6 text-xs text-gray-500">Loading events…</p> : toolsEventsQuery.isError ? <p role="alert" className="py-6 text-xs text-red-600">Event history could not be loaded.</p> : (
                <div className="space-y-1">
                  {toolsEventsQuery.data?.results.map((row) => <button type="button" key={row.id} onClick={() => handleRowSelect(row)} className={`w-full rounded-lg px-2.5 py-2 text-left text-xs ${selectedEventId === row.id ? 'bg-[var(--theme-primary-soft)]' : 'hover:bg-gray-50 dark:hover:bg-zinc-800'}`}>
                    <span className="flex items-center justify-between gap-2"><strong className="truncate text-gray-900 dark:text-white">{row.event_type.replace('_', ' ')} · {row.description}</strong><span className="shrink-0 font-mono">{formatINR(row.amount)}</span></span>
                    <span className="mt-0.5 block text-[10px] text-gray-500">{row.branch_name ?? 'Company-wide'} · {row.source_reference} · {displayDate(row.recorded_at)}</span>
                  </button>)}
                  {!toolsEventsQuery.data?.results.length && <p className="py-6 text-center text-xs text-gray-500">No events found.</p>}
                </div>
              )}
              <div className="mt-2 flex justify-end gap-2">
                <button type="button" disabled={!toolsEventsQuery.data?.previous || toolsPage <= 1} onClick={() => setToolsPage((value) => Math.max(1, value - 1))} className="rounded-full border border-[#e2d8ce] px-2.5 py-1 text-[10px] font-bold disabled:opacity-40 dark:border-zinc-700">Previous</button>
                <button type="button" disabled={!toolsEventsQuery.data?.next} onClick={() => setToolsPage((value) => value + 1)} className="rounded-full border border-[#e2d8ce] px-2.5 py-1 text-[10px] font-bold disabled:opacity-40 dark:border-zinc-700">Next</button>
              </div>
            </div>
            <div className="min-w-0 border-t border-[#f0e7df] pt-3 lg:border-l lg:border-t-0 lg:pl-4 lg:pt-0 dark:border-zinc-800">
              <h3 className="mb-2 text-xs font-bold text-gray-900 dark:text-white">Cash / Bank accounts</h3>
              {accountsQuery.isError ? <p className="text-xs text-red-600">Accounts could not be loaded.</p> : accountsForPage.map((account) => <div key={account.id} className="flex items-center justify-between gap-2 border-b border-[#f0e7df] py-2 text-xs dark:border-zinc-800"><span><strong>{account.label}</strong><span className="ml-1 text-[10px] text-gray-500">{account.account_type}{account.is_active ? '' : ' · archived'}</span></span><span className="flex items-center gap-2">{account.current_balance !== undefined && <span className="font-mono">{formatINR(account.current_balance)}</span>}{isCompanyAccountant && moduleState === 'enabled' && account.is_active && <button type="button" disabled={account.has_history === true || account.current_balance !== '0.00'} title={account.has_history ? 'Accounts with any history cannot be archived.' : 'Only a zero-balance account with no history can be archived.'} onClick={async () => { if (!user || !currentCompany) return; setError(null); try { await accountingMutation(companyId, userId, `accounts/${account.id}/`, 'PATCH', { is_active: false }); await queryClient.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) }); onSuccess?.('Account archived.'); } catch (archiveError) { setError(archiveError instanceof Error ? archiveError.message : 'Account archive failed.'); } }} className="text-[10px] font-bold text-red-600">Archive</button>}</span></div>)}
              <h3 className="mb-2 mt-4 text-xs font-bold text-gray-900 dark:text-white">Shared Company categories</h3>
              {categoriesQuery.isError ? <p className="text-xs text-red-600">Categories could not be loaded.</p> : categories.map((category) => <div key={category.id} className="flex items-center justify-between gap-2 border-b border-[#f0e7df] py-2 text-xs dark:border-zinc-800"><span><strong>{category.label}</strong><span className="ml-1 text-[10px] text-gray-500">{category.kind}{category.is_active ? '' : ' · archived'}</span></span>{isCompanyAccountant && moduleState === 'enabled' && category.is_active && <button type="button" onClick={async () => { if (!user || !currentCompany) return; setError(null); try { await accountingMutation(companyId, userId, `categories/${category.id}/`, 'PATCH', { is_active: false }); await queryClient.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) }); onSuccess?.('Category archived.'); } catch (archiveError) { setError(archiveError instanceof Error ? archiveError.message : 'Category archive failed.'); } }} className="text-[10px] font-bold text-gray-600 dark:text-gray-300">Archive</button>}</div>)}
              {selectedEventId && <div className="mt-4 border-t border-[#f0e7df] pt-3 dark:border-zinc-800">
                <h3 className="text-xs font-bold text-gray-900 dark:text-white">Selected record</h3>
                {selectedEventQuery.isPending ? <p className="mt-2 text-xs text-gray-500">Loading record detail…</p> : selectedEventQuery.isError ? <p className="mt-2 text-xs text-red-600">Record detail could not be loaded.</p> : eventDetail && <EventActions event={eventDetail} canAccount={canAccount} onAction={(action, applicationId) => openForm(action, { event: eventDetail, applicationId })} />}
              </div>}
            </div>
          </div>
          {error && <p role="alert" className="border-t border-red-200 bg-red-50 px-5 py-3 text-xs text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">{error}</p>}
        </ModalFrame>
      )}

      {selectedEventId && !dialog && (
        <ModalFrame title="Accounting record detail" onClose={() => setSelectedEventId(null)}>
          <div className="space-y-3 overflow-y-auto p-5">
            {selectedEventQuery.isPending ? <p className="text-xs text-gray-500">Loading record detail…</p> : selectedEventQuery.isError ? <p role="alert" className="text-xs text-red-600">Record detail could not be loaded.</p> : eventDetail && <>
              <EventSummary event={eventDetail} />
              <EventActions event={eventDetail} canAccount={canAccount} onAction={(action, applicationId) => openForm(action, { event: eventDetail, applicationId })} />
            </>}
            {error && <p role="alert" className="text-xs text-red-700 dark:text-red-300">{error}</p>}
          </div>
        </ModalFrame>
      )}

      {dialog?.mode === 'form' && (
        <ModalFrame title={formTitle[dialog.action]} onClose={() => { if (!submitting) { setDialog(null); setError(null); } }}>
          <form onSubmit={saveForm} className="space-y-3 overflow-y-auto p-5">
            {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">{error}</p>}
            {(dialog.action === 'INCOME' || dialog.action === 'EXPENSE') && <>
              {renderInput('amount', 'Amount (₹)', form.amount, 'number', { min: '0.01', step: '0.01' })}
              {renderSelect('category_id', 'Company category', form.category_id, activeCategories.filter((category) => category.kind === dialog.action).map((category) => ({ id: category.id, label: category.label })))}
              {renderBranchField()}
              {renderInput('description', 'Description', form.description)}
              {renderInput('source_reference', 'Source / reference', form.source_reference)}
              {renderInput('effective_at', 'Effective date and time', form.effective_at, 'datetime-local')}
            </>}
            {(dialog.action === 'RECEIPT' || dialog.action === 'PAYMENT') && <>
              {renderInput('amount', 'Actual amount (₹)', form.amount, 'number', { min: '0.01', step: '0.01' })}
              {renderSelect('target_event_id', dialog.action === 'RECEIPT' ? 'Income to receive against' : 'Expense to pay against', form.target_event_id, availableTargetEvents.map((row) => ({ id: row.id, label: `${row.description} · ${formatINR(row.amount)} · ${row.source_reference}` })))}
              <div className="flex items-center justify-between text-[10px] text-gray-500">
                <span>{targetQuery.data?.count ?? 0} possible records · page {targetPage}</span>
                <span className="flex gap-2"><button type="button" disabled={!targetQuery.data?.previous || targetPage <= 1} onClick={() => setTargetPage((value) => Math.max(1, value - 1))} className="font-bold disabled:opacity-40">Previous</button><button type="button" disabled={!targetQuery.data?.next} onClick={() => setTargetPage((value) => value + 1)} className="font-bold disabled:opacity-40">Next</button></span>
              </div>
              {formTargetQuery.data && <p className="text-[11px] text-gray-500">Outstanding: {formatINR(formTargetQuery.data.outstanding_amount)} · actual cash is recorded separately.</p>}
              {renderSelect('account_id', 'Cash / Bank account', form.account_id, activeAccounts.map((account) => ({ id: account.id, label: `${account.label} (${account.account_type})` })))}
              {renderBranchField()}
              {renderInput('effective_at', 'Actual date and time', form.effective_at, 'datetime-local')}
              {renderInput('description', 'Description', form.description)}
              {renderInput('source_reference', 'Receipt / payment reference', form.source_reference)}
            </>}
            {dialog.action === 'OPENING_BALANCE' && <>
              {renderSelect('account_id', 'Cash / Bank account', form.account_id, activeAccounts.map((account) => ({ id: account.id, label: `${account.label} (${account.account_type})` })))}
              {renderInput('amount', 'Signed opening amount (₹)', form.amount, 'number', { min: '-999999999999999999999999999999999999.99', max: '999999999999999999999999999999999999.99', step: '0.01' })}
              {renderBranchField()}{renderInput('effective_at', 'Opening date and time', form.effective_at, 'datetime-local')}
              {renderInput('reason', 'Reason', form.reason)}{renderInput('source_reference', 'Source / reference', form.source_reference)}
            </>}
            {dialog.action === 'TRANSFER' && <>
              {renderSelect('from_account_id', 'From account', form.from_account_id, activeAccounts.map((account) => ({ id: account.id, label: `${account.label} (${account.account_type})` })))}
              {renderSelect('to_account_id', 'To account', form.to_account_id, activeAccounts.filter((account) => account.id !== form.from_account_id).map((account) => ({ id: account.id, label: `${account.label} (${account.account_type})` })))}
              {renderInput('amount', 'Transfer amount (₹)', form.amount, 'number', { min: '0.01', step: '0.01' })}
              {renderBranchField()}{renderInput('effective_at', 'Transfer date and time', form.effective_at, 'datetime-local')}
              {renderInput('reason', 'Reason', form.reason)}{renderInput('source_reference', 'Source / reference', form.source_reference)}
            </>}
            {(dialog.action === 'ACCOUNT' || dialog.action === 'CATEGORY') && <>
              {dialog.action === 'ACCOUNT' && renderSelect('account_type', 'Account type', form.account_type, [{ id: 'CASH', label: 'Cash' }, { id: 'BANK', label: 'Bank' }])}
              {dialog.action === 'CATEGORY' && renderSelect('kind', 'Category type', form.kind, [{ id: 'INCOME', label: 'Income' }, { id: 'EXPENSE', label: 'Expense' }])}
              {renderInput('label', 'Name', form.label)}
            </>}
            {dialog.action === 'CORRECTION' && eventDetail && <>
              <EventSummary event={eventDetail} />
              <fieldset>
                <legend className={labelClass}>Correction outcome — choose one</legend>
                <div className="grid gap-2 sm:grid-cols-2">
                  {[
                    ['REVERSE_ONLY', 'Reverse only', 'False / duplicate entry'],
                    ['REVERSE_AND_REPLACE', 'Reverse and replace', 'Real event, details need correction'],
                  ].map(([value, label, help]) => <label key={value} className={`cursor-pointer rounded-xl border p-3 text-xs ${form.outcome === value ? 'border-[var(--theme-primary)] bg-[var(--theme-primary-soft)]' : 'border-[#e2d8ce] dark:border-zinc-700'}`}><input className="mr-2" type="radio" name="correction-outcome" value={value} checked={form.outcome === value} onChange={() => update('outcome', value)} required /><strong>{label}</strong><span className="mt-1 block pl-5 text-[10px] text-gray-500">{help}</span></label>)}
                </div>
              </fieldset>
              <fieldset>
                <legend className={labelClass}>Did the real event happen?</legend>
                <div className="flex gap-4 text-xs"><label><input className="mr-1" type="radio" name="event-occurred" value="true" checked={form.event_occurred === 'true'} onChange={() => update('event_occurred', 'true')} required /> Yes</label><label><input className="mr-1" type="radio" name="event-occurred" value="false" checked={form.event_occurred === 'false'} onChange={() => update('event_occurred', 'false')} required /> No</label></div>
              </fieldset>
              {form.outcome === 'REVERSE_AND_REPLACE' && <>
                {renderInput('amount', eventDetail.event_type === 'OPENING_BALANCE' ? 'Replacement signed amount (₹)' : 'Replacement amount (₹)', form.amount, 'number', { min: eventDetail.event_type === 'OPENING_BALANCE' ? '-999999999999999999999999999999999999.99' : '0.01', max: eventDetail.event_type === 'OPENING_BALANCE' ? '999999999999999999999999999999999999.99' : undefined, step: '0.01' })}
                {(eventDetail.event_type === 'INCOME' || eventDetail.event_type === 'EXPENSE') && renderSelect('category_id', 'Replacement Company category', form.category_id, activeCategories.filter((category) => category.kind === eventDetail.event_type).map((category) => ({ id: category.id, label: category.label })))}
                {(eventDetail.event_type === 'RECEIPT' || eventDetail.event_type === 'PAYMENT') && <>
                  {renderSelect('account_id', 'Replacement Cash / Bank account', form.account_id, activeAccounts.map((account) => ({ id: account.id, label: `${account.label} (${account.account_type})` })))}
                  {renderInput('effective_at', 'Correct actual date and time', form.effective_at, 'datetime-local')}
                </>}
                {eventDetail.event_type === 'TRANSFER' && <>
                  {renderSelect('from_account_id', 'From account', form.from_account_id, activeAccounts.map((account) => ({ id: account.id, label: account.label })))}
                  {renderSelect('to_account_id', 'To account', form.to_account_id, activeAccounts.filter((account) => account.id !== form.from_account_id).map((account) => ({ id: account.id, label: account.label })))}
                  {renderInput('effective_at', 'Correct transfer date and time', form.effective_at, 'datetime-local')}
                </>}
                {(eventDetail.event_type === 'INCOME' || eventDetail.event_type === 'EXPENSE' || eventDetail.event_type === 'RECEIPT' || eventDetail.event_type === 'PAYMENT' || eventDetail.event_type === 'TRANSFER') && renderBranchField(eventDetail.branch_id)}
                {renderInput('description', 'Replacement description', form.description)}
                {renderInput('source_reference', 'Replacement source / reference', form.source_reference)}
              </>}
              {renderInput('reason', 'Correction reason', form.reason)}
            </>}
            {dialog.action === 'REALLOCATION' && eventDetail && <>
            {renderSelect('new_target_event_id', 'New Income / Expense target', form.new_target_event_id, availableTargetEvents.map((row) => ({ id: row.id, label: `${row.description} · ${formatINR(row.amount)} · ${row.source_reference}` })))}
              <div className="flex items-center justify-between text-[10px] text-gray-500">
                <span>{targetQuery.data?.count ?? 0} possible records · page {targetPage}</span>
                <span className="flex gap-2"><button type="button" disabled={!targetQuery.data?.previous || targetPage <= 1} onClick={() => setTargetPage((value) => Math.max(1, value - 1))} className="font-bold disabled:opacity-40">Previous</button><button type="button" disabled={!targetQuery.data?.next} onClick={() => setTargetPage((value) => value + 1)} className="font-bold disabled:opacity-40">Next</button></span>
              </div>
              {formTargetQuery.data && <p className="text-[11px] text-gray-500">New target outstanding: {formatINR(formTargetQuery.data.outstanding_amount)}</p>}
              <p className="text-[11px] text-gray-500">The Receipt / Payment and Cash / Bank movement stay unchanged.</p>
              {renderInput('reason', 'Reallocation reason', form.reason)}
            </>}
            {dialog.action !== 'CORRECTION' && dialog.action !== 'REALLOCATION' && !moduleStateAllows(dialog.action, moduleState) && <p role="status" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">This action is disabled while Accounting is {moduleState === 'disabled' ? 'OFF' : 'not configured'}.</p>}
            <div className="flex justify-end gap-2 border-t border-[#f0e7df] pt-3 dark:border-zinc-800">
              <button type="button" onClick={() => setDialog(null)} className="rounded-full border border-[#e2d8ce] px-4 py-2 text-xs font-bold dark:border-zinc-700">Cancel</button>
              <button type="submit" disabled={submitting || !writeStateKnown || !isActionAllowed(dialog.action, moduleState, canAccount, isCompanyAccountant)} className="inline-flex items-center gap-1.5 rounded-full bg-[#18181b] px-4 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"><Check className="h-3.5 w-3.5 text-[var(--theme-primary)]" />{submitting ? 'Saving…' : 'Confirm & Save'}</button>
            </div>
          </form>
        </ModalFrame>
      )}
    </div>
  );

  function renderBranchField(originalBranchId?: string | null) {
    const options = [
      ...(isCompanyAccountant ? [{ id: '__company__', label: 'Company-wide' }] : []),
      ...branches.map((branch) => ({ id: branch.id, label: branch.name })),
    ];
    const value = form.branch_id || (isCompanyAccountant ? '__company__' : originalBranchId ?? '');
    return <div><label className={labelClass} htmlFor="accounting-branch_id">Branch</label><select id="accounting-branch_id" className={inputClass} value={value} required={!isCompanyAccountant} disabled={!isCompanyAccountant && Boolean(originalBranchId)} onChange={(event) => update('branch_id', event.target.value === '__company__' ? '' : event.target.value)}><option value="">{isCompanyAccountant ? 'Company-wide' : 'Select Branch'}</option>{options.filter((option) => option.id !== '__company__').map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></div>;
  }
};

function moduleStateAllows(action: Action, state: AccountingModuleState): boolean {
  if (state === 'enabled') return true;
  return state === 'disabled' && (action === 'RECEIPT' || action === 'PAYMENT' || action === 'CORRECTION' || action === 'REALLOCATION');
}

function isActionAllowed(action: Action, state: AccountingModuleState, canAccount: boolean, isCompanyAccountant: boolean): boolean {
  if (!canAccount) return false;
  if (action === 'ACCOUNT' || action === 'CATEGORY' || action === 'OPENING_BALANCE' || action === 'TRANSFER') return isCompanyAccountant && state === 'enabled';
  return moduleStateAllows(action, state);
}

function EventSummary({ event }: { event: AccountingEventDetail }) {
  return <div className="rounded-xl border border-[#e2d8ce] bg-gray-50 p-3 text-xs dark:border-zinc-700 dark:bg-zinc-800/50"><div className="flex flex-wrap items-center justify-between gap-2"><strong>{event.event_type.replace('_', ' ')} · {event.source_reference}</strong><span className="font-mono font-bold">{event.effect_sign === -1 ? '−' : ''}{formatINR(event.amount)}</span></div><p className="mt-1 text-gray-600 dark:text-gray-300">{event.description}</p><p className="mt-1 text-[10px] text-gray-500">{event.branch_name ?? 'Company-wide'} · Effective {new Date(event.effective_at).toLocaleString('en-IN')} · Recorded {new Date(event.recorded_at).toLocaleString('en-IN')}</p>{event.outstanding_amount !== undefined && <p className="mt-1 text-[10px] text-gray-600 dark:text-gray-300">Outstanding {formatINR(event.outstanding_amount)}</p>}</div>;
}

function EventActions({ event, canAccount, onAction }: {
  event: AccountingEventDetail;
  canAccount: boolean;
  onAction: (action: Action, applicationId?: string) => void;
}) {
  const active = activeApplications(event);
  const current = eventIsCurrent(event);
  return <div className="space-y-3">
    <EventSummary event={event} />
    {event.movements.length > 0 && <div className="text-[11px] text-gray-600 dark:text-gray-300">{event.movements.map((movement) => <p key={movement.id}>{movement.account_label}: {movement.delta}</p>)}</div>}
    {canAccount && current && <div className="flex flex-wrap gap-2">
      {(event.event_type === 'INCOME' || event.event_type === 'EXPENSE') && <button type="button" onClick={() => onAction(event.event_type === 'INCOME' ? 'RECEIPT' : 'PAYMENT')} className="rounded-full border border-[#e2d8ce] px-3 py-1.5 text-[11px] font-bold dark:border-zinc-700">Record {event.event_type === 'INCOME' ? 'Receipt' : 'Payment'}</button>}
      {['INCOME', 'EXPENSE', 'RECEIPT', 'PAYMENT', 'OPENING_BALANCE', 'TRANSFER'].includes(event.event_type) && <button type="button" onClick={() => onAction('CORRECTION')} className="rounded-full bg-[#18181b] px-3 py-1.5 text-[11px] font-bold text-white">Correct</button>}
    </div>}
    {canAccount && current && active.length > 0 && <div><h4 className="mb-1 text-[11px] font-bold">Active cash applications</h4>{active.map((application) => <div key={application.id} className="flex flex-wrap items-center justify-between gap-2 py-1 text-[10px]"><span>{application.source_event_id === event.id ? 'Applied to' : 'Paid / received from'} {application.target_event_id} · {formatINR(application.amount)}</span><button type="button" onClick={() => onAction('REALLOCATION', application.id)} className="font-bold text-[var(--theme-primary)]">Reallocate</button></div>)}</div>}
    {!current && <p className="text-[11px] text-gray-500">Historical record. Its correction chain is preserved; select the current replacement to make a further correction.</p>}
  </div>;
}
