import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { accountingAccounts, accountingCategories } from '../../api/accountingApi';
import { garageApi, GarageCustomerCost } from '../../api/garageApi';
import { queryKeys } from '../../api/queryKeys';
import { GarageCostPaymentCorrection } from './GarageCostPaymentCorrection';

interface Props {
  companyId: string; userId: string; jobId: string; cost: GarageCustomerCost;
  canWrite: boolean; accountingEnabled: boolean; disabled: boolean;
  onBusyChange: (busy: boolean) => void; onClose: () => void;
}

export const GarageCostPayments: React.FC<Props> = ({ companyId, userId, jobId, cost, canWrite, accountingEnabled, disabled, onBusyChange, onClose }) => {
  const client = useQueryClient();
  const [page, setPage] = useState(1);
  const [refundPage, setRefundPage] = useState(1);
  const [adding, setAdding] = useState(false);
  const [refundOpen, setRefundOpen] = useState(false);
  const [amount, setAmount] = useState('');
  const [accountId, setAccountId] = useState('');
  const [effectiveAt, setEffectiveAt] = useState('');
  const [refundAmount, setRefundAmount] = useState('');
  const [refundAccountId, setRefundAccountId] = useState('');
  const [refundEffectiveAt, setRefundEffectiveAt] = useState('');
  const [incomeCategoryId, setIncomeCategoryId] = useState('');
  const [incomeDescription, setIncomeDescription] = useState('');
  const [requestedAmount, setRequestedAmount] = useState('');
  const preview = useQuery({
    queryKey: ['garage', userId, companyId, 'refund-preview', jobId, cost.id, requestedAmount],
    queryFn: ({ signal }) => garageApi.customerCostRefundPreview(companyId, jobId, cost.id, requestedAmount, signal),
    enabled: refundOpen && !!requestedAmount && requestedAmount === refundAmount,
    retry: false, staleTime: 0,
  });
  const hasCurrentPreview = !!refundAmount && requestedAmount === refundAmount && preview.isSuccess && !preview.isFetching;
  const hasExcess = hasCurrentPreview && Number(preview.data.excess_amount) > 0;
  const payments = useQuery({ queryKey: ['garage', userId, companyId, 'cost-payments', jobId, cost.id, page], queryFn: ({ signal }) => garageApi.customerCostPayments(companyId, jobId, cost.id, page, signal), retry: false });
  const refunds = useQuery({ queryKey: ['garage', userId, companyId, 'cost-refunds', jobId, cost.id, refundPage], queryFn: ({ signal }) => garageApi.customerCostRefunds(companyId, jobId, cost.id, refundPage, signal), retry: false });
  const accounts = useQuery({ queryKey: queryKeys.accountingAccounts(userId, companyId), queryFn: ({ signal }) => accountingAccounts(companyId, signal), enabled: (adding || refundOpen) && accountingEnabled && canWrite, retry: false });
  const categories = useQuery({ queryKey: queryKeys.accountingCategories(userId, companyId), queryFn: ({ signal }) => accountingCategories(companyId, signal), enabled: refundOpen && hasExcess && accountingEnabled && canWrite, retry: false });
  const paymentMutation = useMutation({
    mutationFn: () => garageApi.payCustomerCost(companyId, userId, jobId, cost.id, { account_id: accountId, amount, ...(effectiveAt ? { effective_at: new Date(effectiveAt).toISOString() } : {}) }),
    onMutate: () => onBusyChange(true),
    onSuccess: async () => {
      await Promise.all([client.invalidateQueries({ queryKey: ['garage', userId, companyId, 'cost-payments', jobId, cost.id] }), client.invalidateQueries({ queryKey: ['garage', userId, companyId, 'customer-costs', jobId] }), client.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) })]);
      setAdding(false); setAmount(''); setAccountId(''); setEffectiveAt('');
    },
    onSettled: () => onBusyChange(false),
  });
  const refundMutation = useMutation({
    mutationFn: () => garageApi.refundCustomerCost(companyId, userId, jobId, cost.id, {
      account_id: refundAccountId, amount: refundAmount,
      ...(refundEffectiveAt ? { effective_at: new Date(refundEffectiveAt).toISOString() } : {}),
      ...(hasExcess ? { excess_income_category_id: incomeCategoryId, excess_income_description: incomeDescription.trim() } : {}),
    }),
    onMutate: () => onBusyChange(true),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ['garage', userId, companyId, 'cost-refunds', jobId, cost.id] }),
        client.invalidateQueries({ queryKey: ['garage', userId, companyId, 'customer-costs', jobId] }),
        client.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) }),
      ]);
      setRefundOpen(false); setRefundAmount(''); setRefundAccountId(''); setRefundEffectiveAt('');
      setIncomeCategoryId(''); setIncomeDescription(''); setRequestedAmount('');
    },
    onSettled: () => onBusyChange(false),
  });
  const busy = disabled || paymentMutation.isPending || refundMutation.isPending;
  const input = 'w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900';
  const calculateRefund = () => {
    if (!refundAmount) return;
    if (requestedAmount === refundAmount) void preview.refetch();
    else setRequestedAmount(refundAmount);
  };
  return <section aria-label="Cost payments" className="space-y-2 rounded border border-gray-200 p-3 dark:border-zinc-800">
    <div className="flex flex-wrap items-center justify-between gap-2"><h4 className="text-xs font-bold">{cost.description} · Paid ₹{cost.paid} · Refunded ₹{cost.refunded} · Due ₹{cost.payable}</h4><button type="button" disabled={busy} onClick={onClose} className="text-xs">Close payments</button></div>
    {payments.isPending && <p role="status" className="text-xs">Loading payments…</p>}
    {payments.isError && <p role="alert" className="text-xs text-red-600">Payments could not be loaded. <button type="button" onClick={() => void payments.refetch()} className="underline">Retry</button></p>}
    {payments.isSuccess && <><ul className="space-y-3 text-xs">{payments.data.results.map(payment => <li key={payment.id} className="space-y-2"><p>{payment.is_void ? 'Voided payment' : `₹${payment.amount}`} · {new Date(payment.effective_at).toLocaleString()}</p><GarageCostPaymentCorrection companyId={companyId} userId={userId} jobId={jobId} costId={cost.id} payment={payment} canCorrect={canWrite && accountingEnabled} disabled={busy} onBusyChange={onBusyChange} /></li>)}</ul>{payments.data.results.length === 0 && <p className="text-xs text-gray-500">No payments recorded.</p>}<div className="flex gap-3 text-xs"><button type="button" disabled={busy || !payments.data.previous} onClick={() => setPage(p => p - 1)} className="disabled:opacity-40">Previous</button><span>Page {page}</span><button type="button" disabled={busy || !payments.data.next} onClick={() => setPage(p => p + 1)} className="disabled:opacity-40">Next</button></div></>}
    {refunds.isPending && <p role="status" className="text-xs">Loading refunds…</p>}
    {refunds.isError && <p role="alert" className="text-xs text-red-600">Refunds could not be loaded. <button type="button" onClick={() => void refunds.refetch()} className="underline">Retry</button></p>}
    {refunds.isSuccess && <><ul className="space-y-2 text-xs">{refunds.data.results.map(refund => <li key={refund.id} className="border-t border-gray-100 pt-2 dark:border-zinc-800"><p>Refund ₹{refund.amount} · applied to cost ₹{refund.applied_amount} · Income ₹{refund.excess_amount} · {new Date(refund.effective_at).toLocaleString()}</p></li>)}</ul>{refunds.data.results.length === 0 && <p className="text-xs text-gray-500">No refunds recorded.</p>}<div className="flex gap-3 text-xs"><button type="button" disabled={busy || !refunds.data.previous} onClick={() => setRefundPage(p => p - 1)} className="disabled:opacity-40">Previous refunds</button><span>Page {refundPage}</span><button type="button" disabled={busy || !refunds.data.next} onClick={() => setRefundPage(p => p + 1)} className="disabled:opacity-40">Next refunds</button></div></>}
    {canWrite && accountingEnabled && !adding && <button type="button" disabled={busy || Number(cost.payable) <= 0} onClick={() => { paymentMutation.reset(); setAdding(true); }} className="rounded border border-gray-300 px-3 py-2 text-xs disabled:opacity-40">Record cost payment</button>}
    {canWrite && accountingEnabled && !refundOpen && <button type="button" disabled={busy} onClick={() => { refundMutation.reset(); setRefundOpen(true); }} className="rounded border border-gray-300 px-3 py-2 text-xs disabled:opacity-40">Record actual refund</button>}
    {refundOpen && canWrite && accountingEnabled && <form onSubmit={event => { event.preventDefault(); if (!busy && hasCurrentPreview && refundAccountId && (!hasExcess || (incomeCategoryId && incomeDescription.trim()))) refundMutation.mutate(); }} className="space-y-2 rounded border border-gray-200 p-3 dark:border-zinc-800"><fieldset disabled={busy} className="space-y-2">
      <label htmlFor="garage-cost-refund-account" className="block text-xs">Cash / Bank account receiving the refund</label><select id="garage-cost-refund-account" className={input} required value={refundAccountId} onChange={event => setRefundAccountId(event.target.value)}><option value="">Select account</option>{accounts.data?.filter(account => account.is_active).map(account => <option key={account.id} value={account.id}>{account.label} · {account.account_type}</option>)}</select>
      {accounts.isPending && <p role="status" className="text-xs">Loading accounts…</p>}{accounts.isError && <p role="alert" className="text-xs text-red-600">Accounts could not be loaded.</p>}
      <label htmlFor="garage-cost-refund-amount" className="block text-xs">Actual refund amount</label><input id="garage-cost-refund-amount" className={input} type="number" min="0.01" step="0.01" required value={refundAmount} onChange={event => { setRefundAmount(event.target.value); setRequestedAmount(''); refundMutation.reset(); }} />
      <label htmlFor="garage-cost-refund-date" className="block text-xs">Received date and time (optional)</label><input id="garage-cost-refund-date" className={input} type="datetime-local" value={refundEffectiveAt} onChange={event => setRefundEffectiveAt(event.target.value)} />
      <p className="text-xs text-gray-500">Calculation is a preview only; no cash or accounting entry is recorded until you save.</p>
      <button type="button" disabled={!refundAmount || busy} onClick={calculateRefund} className="rounded border border-gray-300 px-3 py-2 text-xs">Calculate refund split</button>
      {preview.isFetching && <p role="status" className="text-xs">Calculating…</p>}
      {preview.isError && requestedAmount === refundAmount && <p role="alert" className="text-xs text-red-600">Refund split could not be calculated. Review the amount and retry.</p>}
      {hasCurrentPreview && <p className="text-xs">Applied to Job cost ₹{preview.data.applied_amount} · Remaining for another record ₹{preview.data.excess_amount}. Posting rechecks these amounts.</p>}
      {hasExcess && <>
        <label htmlFor="garage-refund-income-category" className="block text-xs">Income category for excess amount</label><select id="garage-refund-income-category" className={input} required value={incomeCategoryId} onChange={event => setIncomeCategoryId(event.target.value)}><option value="">Select Income category</option>{categories.data?.filter(category => category.kind === 'INCOME' && category.is_active).map(category => <option key={category.id} value={category.id}>{category.label}</option>)}</select>
        {categories.isPending && <p role="status" className="text-xs">Loading Income categories…</p>}{categories.isError && <p role="alert" className="text-xs text-red-600">Income categories could not be loaded.</p>}
        {categories.isSuccess && categories.data.filter(category => category.kind === 'INCOME' && category.is_active).length === 0 && <p className="text-xs text-amber-700">Create an active Income category in Accounting first, then retry this refund.</p>}
        <label htmlFor="garage-refund-income-note" className="block text-xs">Why is the excess Company Income?</label><textarea id="garage-refund-income-note" className={input} maxLength={500} required value={incomeDescription} onChange={event => setIncomeDescription(event.target.value)} />
        <p className="text-xs text-gray-500">The extra amount is recorded as a separate Income item only after you choose its category and explain it. No automatic Income classification.</p>
      </>}
      {refundMutation.isError && <p role="alert" className="text-xs text-red-600">{refundMutation.error instanceof Error ? refundMutation.error.message : 'Refund could not be saved.'}</p>}
      <div className="flex gap-2"><button type="submit" disabled={busy || !hasCurrentPreview || !refundAccountId || (hasExcess && (!incomeCategoryId || !incomeDescription.trim() || !categories.isSuccess))} className="rounded bg-[var(--theme-primary)] px-3 py-2 text-xs text-white disabled:opacity-40">{refundMutation.isPending ? 'Saving…' : 'Save actual refund'}</button><button type="button" disabled={busy} onClick={() => { setRefundOpen(false); setRequestedAmount(''); }} className="rounded border border-gray-300 px-3 py-2 text-xs">Cancel</button></div>
    </fieldset></form>}
    {adding && canWrite && accountingEnabled && <form onSubmit={event => { event.preventDefault(); if (!busy && accountId && amount) paymentMutation.mutate(); }} className="space-y-2 rounded border border-gray-200 p-3 dark:border-zinc-800"><fieldset disabled={busy} className="space-y-2">
      <label htmlFor="garage-cost-payment-account" className="block text-xs">Cash / Bank account</label><select id="garage-cost-payment-account" className={input} required value={accountId} onChange={event => setAccountId(event.target.value)}><option value="">Select account</option>{accounts.data?.filter(account => account.is_active).map(account => <option key={account.id} value={account.id}>{account.label} · {account.account_type}</option>)}</select>
      {accounts.isPending && <p role="status" className="text-xs">Loading accounts…</p>}{accounts.isError && <p role="alert" className="text-xs text-red-600">Accounts could not be loaded.</p>}
      <label htmlFor="garage-cost-payment-amount" className="block text-xs">Amount</label><input id="garage-cost-payment-amount" className={input} type="number" min="0.01" step="0.01" required value={amount} onChange={event => setAmount(event.target.value)} />
      <label htmlFor="garage-cost-payment-date" className="block text-xs">Paid date and time (optional)</label><input id="garage-cost-payment-date" className={input} type="datetime-local" value={effectiveAt} onChange={event => setEffectiveAt(event.target.value)} />
      <p className="text-xs text-gray-500">Only record money actually paid. Current due ₹{cost.payable}.</p>
      {paymentMutation.isError && <p role="alert" className="text-xs text-red-600">{paymentMutation.error instanceof Error ? paymentMutation.error.message : 'Payment could not be saved.'}</p>}
      <div className="flex gap-2"><button type="submit" disabled={!accountId || !accounts.isSuccess} className="rounded bg-[var(--theme-primary)] px-3 py-2 text-xs text-white disabled:opacity-40">{paymentMutation.isPending ? 'Saving…' : 'Save payment'}</button><button type="button" onClick={() => setAdding(false)} className="rounded border border-gray-300 px-3 py-2 text-xs">Cancel</button></div>
    </fieldset></form>}
  </section>;
};
