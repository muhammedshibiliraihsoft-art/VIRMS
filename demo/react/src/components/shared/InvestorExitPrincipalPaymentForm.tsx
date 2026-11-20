import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { accountingAccounts } from '../../api/accountingApi';
import { authApi } from '../../api/authApi';
import { InvestorExitSettlementPosition, phase5Api } from '../../api/phase5Api';
import { queryKeys } from '../../api/queryKeys';

export function InvestorExitPrincipalPaymentForm({ companyId, userId, investorId, position, onSaved }: {
  companyId: string; userId: string; investorId: string; position: InvestorExitSettlementPosition; onSaved: () => Promise<void>;
}) {
  const client = useQueryClient();
  const [branchId, setBranchId] = useState('');
  const [accountId, setAccountId] = useState('');
  const [amount, setAmount] = useState('');
  const [reference, setReference] = useState('');
  const [effectiveAt, setEffectiveAt] = useState(() => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  });
  const [reason, setReason] = useState('');
  const options = useQuery({
    queryKey: ['companies', userId, companyId, 'phase8', 'exit-payment-inputs'],
    queryFn: async ({ signal }) => {
      const [accounts, branches] = await Promise.all([
        accountingAccounts(companyId, signal),
        (async () => {
          let page = await authApi.phase5Branches(companyId, 1, signal);
          const result = [...page.results];
          for (let n = 2; page.next; n++) { page = await authApi.phase5Branches(companyId, n, signal); result.push(...page.results); }
          return result;
        })(),
      ]);
      return { accounts: accounts.filter((account) => account.is_active), branches };
    }, retry: false,
  });
  const mutation = useMutation({
    mutationFn: () => phase5Api.recordInvestorExitPrincipalPayment(companyId, userId, investorId, position.exit_request_id, {
      branch_id: branchId, account_id: accountId, amount, reference: reference.trim(),
      effective_at: new Date(effectiveAt).toISOString(), expected_source_version: position.source_version, reason: reason.trim(),
    }),
    onSuccess: async () => {
      await onSaved();
      await client.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) });
      await client.invalidateQueries({ queryKey: ['companies', userId, companyId, 'phase5', 'fund-credits'] });
      await client.invalidateQueries({ queryKey: ['companies', userId, companyId, 'phase5', 'fund-summary'] });
      await client.invalidateQueries({ queryKey: ['companies', userId, companyId, 'phase5', 'principal-returns'] });
    },
  });
  const control = 'h-9 min-w-0 rounded-lg border border-gray-200 bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950';
  return <form aria-label="Exit principal payment" className="mt-2 rounded-lg border border-gray-200 p-2.5 dark:border-zinc-700"
    onSubmit={(event) => { event.preventDefault(); if (!mutation.isPending) mutation.mutate(); }}>
    <p className="mb-2 text-[11px] font-bold">Record actual principal paid · available {position.principal_available}</p>
    {options.isPending ? <p role="status" className="text-xs">Loading payment accounts and Branches…</p> : options.isError ?
      <p role="alert" className="text-xs text-red-700">Could not load payment options. <button type="button" onClick={() => void options.refetch()}>Retry</button></p> :
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <select aria-label="Exit payment Branch" className={control} value={branchId} onChange={(e) => setBranchId(e.target.value)} required>
          <option value="">Select Branch</option>{options.data?.branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
        </select>
        <select aria-label="Exit payment Cash / Bank account" className={control} value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
          <option value="">Select Cash / Bank</option>{options.data?.accounts.map((account) => <option key={account.id} value={account.id}>{account.label}</option>)}
        </select>
        <input aria-label="Exit principal amount" className={control} inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} required placeholder="0.00" />
        <input aria-label="Exit payment reference" className={control} value={reference} onChange={(e) => setReference(e.target.value)} required minLength={3} maxLength={200} placeholder="Receipt / bank reference" />
        <input aria-label="Exit payment date" type="datetime-local" className={control} value={effectiveAt} onChange={(e) => setEffectiveAt(e.target.value)} required />
        <input aria-label="Exit payment reason" className={control} value={reason} onChange={(e) => setReason(e.target.value)} required minLength={3} maxLength={500} placeholder="Reason" />
      </div>}
    {mutation.error && <p role="alert" className="mt-2 text-xs text-red-700">{mutation.error instanceof Error ? mutation.error.message : 'Payment failed.'}</p>}
    <div className="mt-2 flex justify-end">
      <button type="submit" disabled={!options.data || !branchId || !accountId || !amount || !reference.trim() || !effectiveAt || reason.trim().length < 3 || mutation.isPending}
        className="h-8 rounded-lg bg-gray-900 px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">{mutation.isPending ? 'Saving…' : 'Record partial payment'}</button>
    </div>
  </form>;
}
