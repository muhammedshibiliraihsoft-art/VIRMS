import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { accountingAccounts } from '../../api/accountingApi';
import { garageApi, GarageCharge, GarageCustomerCost, GarageJob, GarageReceipt } from '../../api/garageApi';
import { queryKeys } from '../../api/queryKeys';
import { GarageCustomerHistory } from './GarageCustomerHistory';
import { GarageCostPayments } from './GarageCostPayments';

type Action = 'charge' | 'cost' | 'costCorrection' | 'receipt';
interface Props { companyId: string; userId: string; job: GarageJob; accountingEnabled: boolean; canWrite?: boolean; disabled?: boolean; onBusyChange?: (busy: boolean) => void }

export const GarageCustomerFinance: React.FC<Props> = ({ companyId, userId, job, accountingEnabled, canWrite = true, disabled = false, onBusyChange }) => {
  const client = useQueryClient();
  const [action, setAction] = useState<Action | null>(null);
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [reference, setReference] = useState('');
  const [accountId, setAccountId] = useState('');
  const [receiptDate, setReceiptDate] = useState('');
  const [costPage, setCostPage] = useState(1);
  const [correctingCost, setCorrectingCost] = useState<GarageCustomerCost | null>(null);
  const [paymentCostId, setPaymentCostId] = useState<string | null>(null);
  const [chargeVersion, setChargeVersion] = useState(0);
  const chargeChanged = action === 'charge' && chargeVersion !== (job.charge_version ?? 0);
  const [history, setHistory] = useState<{ kind: 'charges' | 'receipts' | 'cost'; costId?: string } | null>(null);
  const costs = useQuery({ queryKey: ['garage', userId, companyId, 'customer-costs', job.id, costPage], queryFn: ({ signal }) => garageApi.customerCosts(companyId, job.id, costPage, signal), retry: false });
  const accounts = useQuery({ queryKey: ['garage', userId, companyId, 'accounts'], queryFn: ({ signal }) => accountingAccounts(companyId, signal), enabled: action === 'receipt' && accountingEnabled, retry: false });
  const mutation = useMutation({ mutationFn: async (): Promise<GarageCharge | GarageCustomerCost | GarageReceipt> => {
    if (action === 'charge') {
      if (chargeChanged) throw new Error('The charge changed. Close and reopen the form to review it.');
      return garageApi.charge(companyId, userId, job.id, { amount, expected_version: chargeVersion, reason: description.trim() });
    }
    if (action === 'cost') return garageApi.customerCost(companyId, userId, job.id, { amount, description: description.trim() });
    if (action === 'costCorrection' && correctingCost) return garageApi.correctCustomerCost(companyId, userId, job.id, correctingCost.id, { amount, expected_version: correctingCost.version, reason: description.trim() });
    if (action === 'receipt') return garageApi.receipt(companyId, userId, job.id, { amount, account_id: accountId, reference: reference.trim(), ...(receiptDate ? { effective_at: new Date(receiptDate).toISOString() } : {}) });
    throw new Error('Choose an action.');
  }, onMutate: () => onBusyChange?.(true), onSuccess: async () => {
    if (action === 'receipt') await client.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) });
    await Promise.all([client.invalidateQueries({ queryKey: ['garage', userId, companyId, 'job', job.id] }), client.invalidateQueries({ queryKey: ['garage', userId, companyId, 'customer-costs', job.id] }), client.invalidateQueries({ queryKey: ['garage', userId, companyId, 'history', job.id] })]);
    setAction(null); setAmount(''); setDescription(''); setReference(''); setAccountId(''); setReceiptDate('');
  }, onSettled: () => onBusyChange?.(false) });
  const choose = (next: Action, cost?: GarageCustomerCost) => { mutation.reset(); setAction(next); setChargeVersion(job.charge_version ?? 0); setCorrectingCost(cost ?? null); setAmount(cost?.amount ?? ''); setDescription(''); setReference(''); setAccountId(''); setReceiptDate(''); };
  const activeAccounts = accounts.data?.filter(account => account.is_active) ?? [];
  return <div className="space-y-3 border-t border-gray-100 pt-3 dark:border-zinc-800">
    <h3 className="text-xs font-bold">Customer job amounts</h3>
    <p className="text-xs text-gray-500">Recorded cost ₹{job.customer_cost_total ?? '0.00'}</p>
    <p className="text-xs text-gray-500">Recorded costs do not automatically change the customer charge.</p>
    <div className="flex flex-wrap gap-2 text-xs"><button type="button" disabled={disabled || mutation.isPending} onClick={() => setHistory({ kind: 'charges' })} className="rounded border border-gray-300 px-2 py-1">Charge history</button><button type="button" disabled={disabled || mutation.isPending} onClick={() => setHistory({ kind: 'receipts' })} className="rounded border border-gray-300 px-2 py-1">Receipt history</button></div>
    {costs.isPending && <p role="status" className="text-xs">Loading costs…</p>}{costs.isError && <p role="alert" className="text-xs text-red-600">Costs could not be loaded.</p>}
    {costs.isSuccess && <><ul className="space-y-2 text-xs">{costs.data.results.map(cost => <li key={cost.id} className="flex flex-wrap items-center justify-between gap-2"><span>{cost.description} · ₹{cost.amount} · Paid ₹{cost.paid} · Due ₹{cost.payable}</span><span className="flex flex-wrap gap-2"><button type="button" disabled={disabled || mutation.isPending} onClick={() => setHistory({ kind: 'cost', costId: cost.id })} className="rounded border border-gray-300 px-2 py-1">History</button><button type="button" disabled={disabled || mutation.isPending} onClick={() => { setPaymentCostId(cost.id); setAction(null); }} className="rounded border border-gray-300 px-2 py-1">Payments</button>{canWrite && job.status === 'OPEN' && <button type="button" disabled={disabled || mutation.isPending} onClick={() => choose('costCorrection', cost)} className="rounded border border-gray-300 px-2 py-1">Correct</button>}</span></li>)}</ul>{costs.data.results.length === 0 && <p className="text-xs text-gray-500">No customer job costs.</p>}<div className="flex gap-3 text-xs"><button type="button" disabled={disabled || !costs.data.previous} onClick={() => { setPaymentCostId(null); setCostPage(p => p - 1); }} className="disabled:opacity-40">Previous</button><span>Page {costPage}</span><button type="button" disabled={disabled || !costs.data.next} onClick={() => { setPaymentCostId(null); setCostPage(p => p + 1); }} className="disabled:opacity-40">Next</button></div></>}
    {paymentCostId && costs.data?.results.find(cost => cost.id === paymentCostId) && <GarageCostPayments key={paymentCostId} companyId={companyId} userId={userId} jobId={job.id} cost={costs.data.results.find(cost => cost.id === paymentCostId)!} canWrite={canWrite} accountingEnabled={accountingEnabled} disabled={disabled || mutation.isPending} onBusyChange={onBusyChange ?? (() => {})} onClose={() => setPaymentCostId(null)} />}
    {history && <GarageCustomerHistory key={`${history.kind}:${history.costId ?? ''}`} companyId={companyId} userId={userId} jobId={job.id} kind={history.kind} costId={history.costId} canCorrect={canWrite && accountingEnabled} disabled={disabled || mutation.isPending} onBusyChange={onBusyChange} onClose={() => setHistory(null)} />}
    {canWrite && <fieldset disabled={disabled} className="space-y-3"><div className="flex flex-wrap gap-2 text-xs">
      {job.status === 'OPEN' && <><button type="button" disabled={mutation.isPending} onClick={() => choose('charge')} className="rounded border border-gray-300 px-3 py-2">{job.customer_charge == null ? 'Set charge' : 'Correct charge'}</button><button type="button" disabled={mutation.isPending} onClick={() => choose('cost')} className="rounded border border-gray-300 px-3 py-2">Add cost</button></>}
      {accountingEnabled && job.customer_charge != null && <button type="button" disabled={mutation.isPending} onClick={() => choose('receipt')} className="rounded border border-gray-300 px-3 py-2">Record receipt</button>}
    </div>
    {action && <form onSubmit={event => { event.preventDefault(); if (!mutation.isPending && !chargeChanged) mutation.mutate(); }} className="space-y-2 rounded border border-gray-200 p-3 dark:border-zinc-800">
      <h4 className="text-xs font-semibold">{action === 'charge' ? 'Customer charge' : action === 'cost' ? 'Customer job cost' : action === 'costCorrection' ? `Correct ${correctingCost?.description ?? 'cost'}` : 'Customer receipt'}</h4>
      <fieldset disabled={mutation.isPending} className="space-y-2">
        <label htmlFor="garage-finance-amount" className="block text-xs">Amount</label><input id="garage-finance-amount" type="number" min={action === 'charge' ? '0' : '0.01'} step="0.01" required value={amount} onChange={event => setAmount(event.target.value)} className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" />
        {action !== 'receipt' && <><label htmlFor="garage-finance-description" className="block text-xs">{action === 'cost' ? 'Description' : 'Reason for correction'}</label><input id="garage-finance-description" value={description} onChange={event => setDescription(event.target.value)} required={action === 'cost' || action === 'costCorrection' || (job.charge_version ?? 0) > 0} maxLength={500} className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" />{action === 'cost' && <p className="text-xs text-gray-500">Records the cost; it does not record a payment.</p>}</>}
        {action === 'receipt' && <><label htmlFor="garage-receipt-account" className="block text-xs">Cash / Bank account</label><select id="garage-receipt-account" value={accountId} onChange={event => setAccountId(event.target.value)} required className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900"><option value="">Select account</option>{activeAccounts.map(account => <option key={account.id} value={account.id}>{account.label} · {account.account_type}</option>)}</select>{accounts.isPending && <p role="status" className="text-xs">Loading accounts…</p>}{accounts.isError && <p role="alert" className="text-xs text-red-600">Accounts could not be loaded.</p>}<label htmlFor="garage-receipt-reference" className="block text-xs">Receipt reference</label><input id="garage-receipt-reference" required maxLength={200} value={reference} onChange={event => setReference(event.target.value)} className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" /><label htmlFor="garage-receipt-date" className="block text-xs">Received date and time (optional)</label><input id="garage-receipt-date" type="datetime-local" value={receiptDate} onChange={event => setReceiptDate(event.target.value)} className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" /><p className="text-xs text-gray-500">Leave blank to use the current time. Only record money actually received. Outstanding ₹{job.outstanding ?? '—'}.</p></>}
        {chargeChanged && <p role="alert" className="text-xs text-red-600">The charge changed. Cancel and reopen the form to review the latest amount.</p>}
        {mutation.isError && <p role="alert" className="text-xs text-red-600">{mutation.error instanceof Error ? mutation.error.message : 'Could not save.'}</p>}
        <div className="flex gap-2"><button type="submit" disabled={chargeChanged || (action === 'receipt' && (!accounts.isSuccess || !accountId))} className="rounded bg-[var(--theme-primary)] px-3 py-2 text-xs text-white disabled:opacity-40">{mutation.isPending ? 'Saving…' : 'Save'}</button><button type="button" onClick={() => setAction(null)} className="rounded border border-gray-300 px-3 py-2 text-xs">Cancel</button></div>
      </fieldset>
    </form>}</fieldset>}
  </div>;
};
