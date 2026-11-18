import React, { useId, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { accountingAccounts } from '../../api/accountingApi';
import { garageApi, LabourPayment } from '../../api/garageApi';
import { queryKeys } from '../../api/queryKeys';

interface Props { companyId: string; userId: string; personId: string; payment: LabourPayment; canCorrect: boolean; disabled?: boolean; onBusyChange: (busy: boolean) => void }

function localTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

export const LabourPaymentCorrection: React.FC<Props> = ({ companyId, userId, personId, payment, canCorrect, disabled = false, onBusyChange }) => {
  const client = useQueryClient();
  const formId = useId();
  const [mode, setMode] = useState<'' | 'REVERSE_ONLY' | 'REVERSE_AND_REPLACE'>('');
  const [open, setOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [reason, setReason] = useState('');
  const [accountId, setAccountId] = useState('');
  const [amount, setAmount] = useState(payment.amount);
  const [effectiveAt, setEffectiveAt] = useState(() => localTime(payment.effective_at));
  const [confirmed, setConfirmed] = useState(false);
  const [snapshot, setSnapshot] = useState<{ eventId: string; effectiveAt: string } | null>(null);
  const changed = open && snapshot !== null && (snapshot.eventId !== payment.event_id || !!payment.is_void);
  const history = useQuery({ queryKey: ['labour', userId, companyId, 'corrections', personId, payment.id, page], queryFn: ({ signal }) => garageApi.labourCorrectionHistory(companyId, personId, payment.id, page, signal), enabled: historyOpen, retry: false });
  const accounts = useQuery({ queryKey: queryKeys.accountingAccounts(userId, companyId), queryFn: ({ signal }) => accountingAccounts(companyId, signal), enabled: open && mode === 'REVERSE_AND_REPLACE' && canCorrect, retry: false });
  const mutation = useMutation({ mutationFn: () => {
    if (!mode || !confirmed || !reason.trim() || !snapshot || changed) throw new Error('Choose the correction and confirm it.');
    const replacement = mode === 'REVERSE_AND_REPLACE' ? { account_id: accountId, amount, effective_at: effectiveAt === localTime(snapshot.effectiveAt) ? snapshot.effectiveAt : new Date(effectiveAt).toISOString() } : undefined;
    return garageApi.correctLabourPayment(companyId, userId, personId, payment.id, { expected_event_id: snapshot.eventId, outcome: mode, reason: reason.trim(), ...(replacement ? { replacement } : {}) });
  }, onMutate: () => onBusyChange(true), onSuccess: async () => {
    await Promise.all([client.invalidateQueries({ queryKey: ['labour', userId, companyId, 'payments', personId] }), client.invalidateQueries({ queryKey: ['labour', userId, companyId, 'corrections', personId, payment.id] }), client.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) })]);
    setOpen(false); setMode(''); setReason(''); setConfirmed(false); setAccountId('');
  }, onSettled: () => onBusyChange(false) });
  const input = 'w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900';
  return <div className="space-y-2"><div className="flex flex-wrap gap-2"><button type="button" onClick={() => setHistoryOpen(value => !value)} className="rounded border border-gray-300 px-2 py-1 text-xs">{historyOpen ? 'Hide correction history' : 'Correction history'}</button>{canCorrect && !payment.is_void && <button type="button" disabled={disabled || mutation.isPending} onClick={() => { mutation.reset(); setMode(''); setReason(''); setAccountId(''); setAmount(payment.amount); setEffectiveAt(localTime(payment.effective_at)); setConfirmed(false); setSnapshot({ eventId: payment.event_id, effectiveAt: payment.effective_at }); setOpen(true); }} className="rounded border border-gray-300 px-2 py-1 text-xs">Correct payment</button>}</div>
    {historyOpen && <div className="space-y-1 text-xs">{history.isPending && <p role="status">Loading correction history…</p>}{history.isError && <p role="alert" className="text-red-600">Correction history could not be loaded.</p>}{history.isSuccess && <>{history.data.results.length === 0 && <p className="text-gray-500">No corrections.</p>}<ol className="space-y-1">{history.data.results.map(row => <li key={row.id}>₹{row.previous_amount} → {row.replacement_amount === null ? 'Voided' : `₹${row.replacement_amount}`} · {row.reason} · {new Date(row.created_at).toLocaleString()}</li>)}</ol><div className="flex gap-3"><button type="button" disabled={!history.data.previous} onClick={() => setPage(p => p - 1)} className="disabled:opacity-40">Previous</button><span>Page {page}</span><button type="button" disabled={!history.data.next} onClick={() => setPage(p => p + 1)} className="disabled:opacity-40">Next</button></div></>}</div>}
    {changed && <p role="alert" className="text-xs text-red-600">This payment changed. Close this form and reopen it to review the latest details. <button type="button" onClick={() => setOpen(false)} className="underline">Close form</button></p>}
    {open && canCorrect && !payment.is_void && <form onSubmit={event => { event.preventDefault(); if (!disabled && !changed && !mutation.isPending) mutation.mutate(); }} className="space-y-2 rounded border border-gray-200 p-3 dark:border-zinc-800"><fieldset disabled={disabled || mutation.isPending} className="space-y-2"><h4 className="text-xs font-bold">Correct payment ₹{payment.amount}</h4><label htmlFor={`${formId}-mode`} className="block text-xs">What happened?</label><select id={`${formId}-mode`} required value={mode} onChange={event => { setMode(event.target.value as typeof mode); setConfirmed(false); }} className={input}><option value="">Choose an option</option><option value="REVERSE_AND_REPLACE">Payment happened; correct its details</option><option value="REVERSE_ONLY">Payment did not happen or was duplicated</option></select>
      {mode === 'REVERSE_AND_REPLACE' && <><label htmlFor={`${formId}-account`} className="block text-xs">Actual Cash / Bank account</label><select id={`${formId}-account`} required value={accountId} onChange={event => setAccountId(event.target.value)} className={input}><option value="">Select account</option>{accounts.data?.filter(row => row.is_active).map(row => <option key={row.id} value={row.id}>{row.label} · {row.account_type}</option>)}</select>{accounts.isPending && <p role="status" className="text-xs">Loading accounts…</p>}{accounts.isError && <p role="alert" className="text-xs text-red-600">Accounts could not be loaded.</p>}<label htmlFor={`${formId}-amount`} className="block text-xs">Actual amount</label><input id={`${formId}-amount`} type="number" min="0.01" step="0.01" required value={amount} onChange={event => setAmount(event.target.value)} className={input} /><label htmlFor={`${formId}-date`} className="block text-xs">Actual payment date and time</label><input id={`${formId}-date`} type="datetime-local" required value={effectiveAt} onChange={event => setEffectiveAt(event.target.value)} className={input} /></>}
      <label htmlFor={`${formId}-reason`} className="block text-xs">Reason</label><input id={`${formId}-reason`} required maxLength={500} value={reason} onChange={event => setReason(event.target.value)} className={input} /><label className="flex items-start gap-2 text-xs"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} required /><span>I checked the actual payment and confirm this correction.</span></label>{mutation.isError && <p role="alert" className="text-xs text-red-600">{mutation.error instanceof Error ? mutation.error.message : 'Correction failed.'}</p>}<div className="flex gap-2"><button type="submit" disabled={changed || !mode || !confirmed || (mode === 'REVERSE_AND_REPLACE' && (!accounts.isSuccess || !accountId))} className="rounded bg-[var(--theme-primary)] px-3 py-2 text-xs text-white disabled:opacity-40">Confirm correction</button><button type="button" onClick={() => setOpen(false)} className="rounded border border-gray-300 px-3 py-2 text-xs">Cancel</button></div></fieldset></form>}
  </div>;
};
