import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../auth/AuthContext';
import { useAccountingAccounts, useAccountingBranches, useAccountingResult } from '../../api/accountingQueries';
import { companyPeriodConfirmations, confirmCompanyPeriod, recordOwnerDistributionPayment } from '../../api/accountingApi';

type ReportingPeriod = 'monthly' | 'h1' | 'h2' | 'annual';

function formatINR(value: string | undefined): string {
  const match = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(value ?? '');
  if (!match) return '—';
  const whole = BigInt(match[2]).toLocaleString('en-IN');
  const paise = (match[3] ?? '').padEnd(2, '0');
  return `₹${match[1]}${whole}.${paise}`;
}

function formatDate(value: string | undefined): string {
  if (!value) return '—';
  const parsed = new Date(`${value.slice(0, 10)}T00:00:00+05:30`);
  return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'Asia/Kolkata' }).format(parsed);
}

function maxDistributableAfterLoss(result: string | undefined, priorLoss: string | undefined): string | undefined {
  if (!result || !/^-?\d+\.\d{2}$/.test(result)) return undefined;
  const loss = priorLoss && /^\d+\.\d{2}$/.test(priorLoss) ? priorLoss : '0.00';
  const cents = (value: string) => {
    const negative = value.startsWith('-'); const unsigned = negative ? value.slice(1) : value;
    const [whole, paise] = unsigned.split('.'); const amount = BigInt(whole) * 100n + BigInt(paise);
    return negative ? -amount : amount;
  };
  const available = cents(result) - cents(loss);
  return `${available > 0n ? available / 100n : 0n}.${String(available > 0n ? available % 100n : 0n).padStart(2, '0')}`;
}

export const CompanyResultView: React.FC = () => {
  const { user, currentCompany } = useAuth();
  const queryClient = useQueryClient();
  const branchesQuery = useAccountingBranches();
  const accountsQuery = useAccountingAccounts();
  const isCompanyWideReader = Boolean(currentCompany?.company_wide_roles?.some((role) => role === 'accountant' || role === 'owner'));
  const [period, setPeriod] = useState<ReportingPeriod>('annual');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [branchId, setBranchId] = useState(isCompanyWideReader ? 'all' : '');
  const branches = useMemo(() => branchesQuery.data ?? [], [branchesQuery.data]);

  useEffect(() => {
    if (isCompanyWideReader && branchId === '') {
      setBranchId('all');
    } else if (!isCompanyWideReader && branchId === 'all') {
      setBranchId(branches.length === 1 ? branches[0].id : '');
    } else if (!isCompanyWideReader && !branchId && branches.length === 1) {
      setBranchId(branches[0].id);
    }
  }, [branchId, branches, isCompanyWideReader]);

  const reportBranchId = branchId && branchId !== 'all' ? branchId : undefined;
  const reportReady = Boolean(currentCompany && (isCompanyWideReader || reportBranchId));
  const reportQuery = useAccountingResult({
    period,
    year,
    month: period === 'monthly' ? month : undefined,
    branchId: reportBranchId,
    enabled: reportReady,
  });
  const report = reportQuery.data;
  const canConfirmPeriod = Boolean(currentCompany?.company_wide_roles?.includes('accountant'));
  const periodKey = currentCompany ? ['companies', currentCompany.id, 'company-period-confirmations'] : ['company-period-confirmations-unavailable'];
  const confirmationsQuery = useQuery({
    queryKey: periodKey,
    queryFn: ({ signal }) => currentCompany ? companyPeriodConfirmations(currentCompany.id, signal) : Promise.reject(new Error('Company required.')),
    enabled: Boolean(currentCompany && canConfirmPeriod), retry: false,
  });
  const [distributable, setDistributable] = useState('');
  const [liabilityReviewReason, setLiabilityReviewReason] = useState('');
  const [confirmationReason, setConfirmationReason] = useState('');
  const [payoutRecipientId, setPayoutRecipientId] = useState('');
  const [payoutBranchId, setPayoutBranchId] = useState('');
  const [payoutAccountId, setPayoutAccountId] = useState('');
  const [payoutAmount, setPayoutAmount] = useState('');
  const [payoutReason, setPayoutReason] = useState('');
  const confirmationMutation = useMutation({
    mutationFn: () => currentCompany && report?.source_version && period !== 'monthly' && report.period_start && user
      ? confirmCompanyPeriod(currentCompany.id, user.id, {
        period_type: period, year, expected_source_version: report.source_version,
        distributable_amount: distributable, liabilities_reviewed: true,
        liability_review_reason: liabilityReviewReason, reason: confirmationReason,
      }) : Promise.reject(new Error('Reload the Company-wide result and review liabilities first.')),
    onSuccess: async () => { setDistributable(''); setLiabilityReviewReason(''); setConfirmationReason(''); await queryClient.invalidateQueries({ queryKey: periodKey }); },
  });
  const confirmed = report ? confirmationsQuery.data?.confirmations.find((row) => row.period_start === report.period_start && row.period_end === report.period_end) : undefined;
  const accounts = (accountsQuery.data ?? []).filter((account) => account.is_active);
  const selectedPayoutBranchId = payoutBranchId || (branchId !== 'all' ? branchId : branches[0]?.id ?? '');
  const selectedPayoutAccountId = payoutAccountId || accounts[0]?.id || '';
  const payableAllocations = (confirmed?.owner_allocation_snapshot ?? []).filter((allocation) => Number(allocation.outstanding_amount ?? allocation.amount) > 0);
  const selectedAllocation = payableAllocations.find((allocation) => allocation.recipient_id === payoutRecipientId) ?? payableAllocations[0];
  const payoutMutation = useMutation({
    mutationFn: () => currentCompany && user && confirmed && selectedAllocation && selectedPayoutBranchId && selectedPayoutAccountId
      ? recordOwnerDistributionPayment(currentCompany.id, user.id, confirmed.id, {
        recipient_id: selectedAllocation.recipient_id, branch_id: selectedPayoutBranchId, account_id: selectedPayoutAccountId,
        amount: payoutAmount || selectedAllocation.outstanding_amount || selectedAllocation.amount,
        effective_at: new Date().toISOString(), expected_source_version: confirmed.source_version, reason: payoutReason,
      }) : Promise.reject(new Error('Choose an Owner, Branch and Cash/Bank account from the current Company period.')),
    onSuccess: async () => { setPayoutAmount(''); setPayoutReason(''); await queryClient.invalidateQueries({ queryKey: periodKey }); },
  });
  const priorConfirmation = report ? confirmationsQuery.data?.confirmations
    .filter((row) => row.period_end <= report.period_start)
    .sort((a, b) => b.period_end.localeCompare(a.period_end))[0] : undefined;
  const maxDistributable = report ? maxDistributableAfterLoss(report.accounting_result_amount, priorConfirmation?.loss_carried_forward) : undefined;
  const submitPeriodConfirmation = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); confirmationMutation.mutate(); };

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-3.5 pb-8" aria-label="Company Accounting Result">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-[#f2ebe5] pb-3 dark:border-zinc-800">
        <div className="min-w-0">
          <p className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">Company finance · source report</p>
          <h1 className="mt-0.5 text-xl font-extrabold tracking-tight text-gray-950 dark:text-white sm:text-2xl">Company Accounting Result</h1>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Recognized Accounting Income minus Expense for the selected window.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select aria-label="Reporting period" value={period} onChange={(event) => setPeriod(event.target.value as ReportingPeriod)} className="h-9 rounded-lg border border-[#e2d8ce] bg-white px-2 text-xs font-semibold dark:border-zinc-700 dark:bg-zinc-900">
            <option value="monthly">Monthly</option><option value="h1">H1</option><option value="h2">H2</option><option value="annual">Annual</option>
          </select>
          <input aria-label="Reporting year" type="number" min="1900" max="9998" value={year} onChange={(event) => setYear(Number(event.target.value))} className="h-9 w-20 rounded-lg border border-[#e2d8ce] bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-900" />
          {period === 'monthly' && <select aria-label="Reporting month" value={month} onChange={(event) => setMonth(Number(event.target.value))} className="h-9 rounded-lg border border-[#e2d8ce] bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-900">
            {Array.from({ length: 12 }, (_, index) => <option key={index + 1} value={index + 1}>{new Intl.DateTimeFormat('en', { month: 'short' }).format(new Date(2000, index, 1))}</option>)}
          </select>}
          <label className="flex items-center gap-1.5 text-[10px] font-bold text-gray-500 dark:text-gray-400">
            Branch
            <select aria-label="Result Branch" value={branchId} onChange={(event) => setBranchId(event.target.value)} disabled={branchesQuery.isPending || branchesQuery.isError} className="h-9 max-w-44 rounded-lg border border-[#e2d8ce] bg-white px-2 text-xs font-semibold text-gray-900 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-900 dark:text-white">
              {isCompanyWideReader && <option value="all">All authorized Branches</option>}
              {!isCompanyWideReader && <option value="">Select Branch</option>}
              {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
            </select>
          </label>
        </div>
      </header>

      {branchesQuery.isError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">Authorized Branches could not be loaded. Refresh and try again.</p>}
      {branchesQuery.isPending && <p role="status" className="text-xs text-gray-500">Loading authorized Branches…</p>}
      {!branchesQuery.isPending && !branchesQuery.isError && !reportReady && <p role="status" className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">Select an authorized Branch to view this report.</p>}
      {reportQuery.isPending && reportReady && <p role="status" className="text-xs text-gray-500">Loading verified Accounting result…</p>}
      {reportQuery.isError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">Accounting result could not be loaded. No sample values are shown.</p>}
      {report && <>
        <section className="grid gap-2 sm:grid-cols-3" aria-label="Accounting result values">
          {[
            ['Recognized Income', report.income_amount],
            ['Recognized Expense', report.expense_amount],
            ['Accounting Result', report.accounting_result_amount],
          ].map(([label, value], index) => <article key={label} className={`rounded-2xl border p-3.5 ${index === 2 ? 'border-zinc-900 bg-zinc-900 text-white dark:border-white dark:bg-white dark:text-zinc-950' : 'border-[#eee6de] bg-white text-gray-950 dark:border-zinc-800 dark:bg-zinc-900 dark:text-white'}`}>
            <p className={`text-[11px] font-semibold ${index === 2 ? 'opacity-75' : 'text-gray-500 dark:text-gray-400'}`}>{label}</p>
            <p className="mt-1 text-xl font-extrabold tabular-nums">{formatINR(value)}</p>
          </article>)}
        </section>
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] leading-5 text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
          {formatDate(report.starts_at)} through {formatDate(report.ends_before)} (exclusive), {report.timezone}. This is the Accounting Income − Expense result; it is not the final distributable Company Profit and does not include an unrecognized Vehicle Company Share or Garage Revenue.
        </p>
        {canConfirmPeriod && period !== 'monthly' && <section className="rounded-xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900" aria-label="Company period distributable confirmation">
          <h2 className="text-sm font-bold">Confirm Company distributable amount</h2>
          <p className="mt-1 text-[11px] text-gray-600 dark:text-gray-300">Accountant reviews liabilities and records the amount available after prior Company Loss. This confirmation creates no payment.</p>
          {maxDistributable !== undefined && <p className="mt-1 text-[11px]">Prior Loss: <strong>{formatINR(priorConfirmation?.loss_carried_forward ?? '0.00')}</strong> · maximum after Loss: <strong>{formatINR(maxDistributable)}</strong></p>}
          {confirmationsQuery.isError && <p role="alert" className="mt-2 text-xs text-red-700">Company period history could not be loaded.</p>}
          {confirmationsQuery.isPending && <p role="status" className="mt-2 text-[11px]">Loading confirmed Company period…</p>}
          {confirmed && <p className="mt-2 text-xs">{confirmed.source_current === false ? <strong className="text-amber-700">Sources changed · reconfirm required</strong> : 'Confirmed'} · distributable: <strong>{formatINR(confirmed.distributable_amount)}</strong> · Loss carried forward: <strong>{formatINR(confirmed.loss_carried_forward)}</strong> · Version {confirmed.version}</p>}
          {confirmed?.owner_allocation_snapshot.length ? <ul className="mt-2 grid gap-1 text-[11px] sm:grid-cols-2" aria-label="Owner distribution allocation snapshot">
            {confirmed.owner_allocation_snapshot.map((allocation) => <li key={allocation.recipient_id} className="flex justify-between gap-2 rounded-md bg-gray-50 px-2 py-1 dark:bg-zinc-800"><span>{allocation.recipient_label} · {allocation.percentage}%{allocation.paid_amount ? ` · paid ${formatINR(allocation.paid_amount)}` : ''}</span><strong>{formatINR(allocation.outstanding_amount ?? allocation.amount)}</strong></li>)}
          </ul> : confirmed && Number(confirmed.distributable_amount) > 0 ? <p className="mt-2 text-[11px] text-amber-700">Owner split is not available for this confirmation.</p> : null}
          {canConfirmPeriod && confirmed?.source_current && payableAllocations.length > 0 && <form className="mt-3 grid gap-2 border-t border-gray-200 pt-3 sm:grid-cols-2 dark:border-zinc-700" aria-label="Record partial Owner distribution payment" onSubmit={(event) => { event.preventDefault(); if (payoutReason.trim().length >= 3 && selectedPayoutBranchId && selectedPayoutAccountId) payoutMutation.mutate(); }}>
            <label className="text-[10px] font-bold">Owner<select value={selectedAllocation?.recipient_id ?? ''} onChange={(event) => { setPayoutRecipientId(event.target.value); setPayoutAmount(''); }} className="mt-1 block h-9 w-full rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950">
              {payableAllocations.map((allocation) => <option key={allocation.recipient_id} value={allocation.recipient_id}>{allocation.recipient_label} · outstanding {formatINR(allocation.outstanding_amount ?? allocation.amount)}</option>)}
            </select></label>
            <label className="text-[10px] font-bold">Payment amount<input type="number" min="0.01" step="0.01" max={selectedAllocation?.outstanding_amount ?? selectedAllocation?.amount} required value={payoutAmount || selectedAllocation?.outstanding_amount || selectedAllocation?.amount || ''} onChange={(event) => setPayoutAmount(event.target.value)} className="mt-1 block h-9 w-full rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950" /></label>
            <label className="text-[10px] font-bold">Paid from Branch<select required value={selectedPayoutBranchId} onChange={(event) => setPayoutBranchId(event.target.value)} className="mt-1 block h-9 w-full rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950"><option value="">Select Branch</option>{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label>
            <label className="text-[10px] font-bold">Cash/Bank account<select required value={selectedPayoutAccountId} onChange={(event) => setPayoutAccountId(event.target.value)} className="mt-1 block h-9 w-full rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950"><option value="">Select account</option>{accounts.map((account) => <option key={account.id} value={account.id}>{account.label} · {account.account_type}</option>)}</select></label>
            <label className="text-[10px] font-bold sm:col-span-2">Payment reason<input required minLength={3} maxLength={500} value={payoutReason} onChange={(event) => setPayoutReason(event.target.value)} className="mt-1 block h-9 w-full rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950" /></label>
            <button type="submit" disabled={payoutMutation.isPending || accountsQuery.isPending || branchesQuery.isPending || !accounts.length || !branches.length || payoutReason.trim().length < 3} className="h-9 rounded-lg bg-gray-900 px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">{payoutMutation.isPending ? 'Recording…' : 'Record Owner payment'}</button>
            {(accountsQuery.isError || branchesQuery.isError) && <p role="alert" className="self-center text-[10px] text-red-700">Branch or Cash/Bank list could not be loaded.</p>}
            {payoutMutation.error && <p role="alert" className="sm:col-span-2 text-xs text-red-700">{payoutMutation.error instanceof Error ? payoutMutation.error.message : 'Owner payment failed.'}</p>}
          </form>}
          {report.source_version && <form className="mt-2 grid gap-2 sm:grid-cols-2" onSubmit={submitPeriodConfirmation}>
            <input aria-label="Confirmed distributable amount" className="h-9 rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950" inputMode="decimal" value={distributable} onChange={(event) => setDistributable(event.target.value)} required placeholder="Distributable amount" />
            <input aria-label="Liability review reason" className="h-9 rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950" value={liabilityReviewReason} onChange={(event) => setLiabilityReviewReason(event.target.value)} required minLength={3} maxLength={500} placeholder="Liabilities reviewed · reason" />
            <input aria-label="Company period confirmation reason" className="h-9 rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950" value={confirmationReason} onChange={(event) => setConfirmationReason(event.target.value)} required minLength={3} maxLength={500} placeholder="Confirmation reason" />
            <button type="submit" disabled={confirmationMutation.isPending || !distributable || liabilityReviewReason.trim().length < 3 || confirmationReason.trim().length < 3} className="h-9 rounded-lg bg-gray-900 px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">{confirmationMutation.isPending ? 'Saving…' : 'Confirm period amount'}</button>
          </form>}
          {confirmationMutation.error && <p role="alert" className="mt-2 text-xs text-red-700">{confirmationMutation.error instanceof Error ? confirmationMutation.error.message : 'Company period confirmation failed.'}</p>}
        </section>}
      </>}
    </main>
  );
};
