import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { accountingAccounts } from '../../api/accountingApi';
import { authApi } from '../../api/authApi';
import { InvestorExitSettlementPosition, phase5Api } from '../../api/phase5Api';
import { queryKeys } from '../../api/queryKeys';

export function InvestorExitLossApplicationForm({ companyId, userId, investorId, position, onSaved }: {
  companyId: string; userId: string; investorId: string; position: InvestorExitSettlementPosition; onSaved: () => Promise<void>;
}) {
  const client = useQueryClient();
  const [lossResultId, setLossResultId] = useState(position.confirmed_losses[0]?.loss_result_id ?? '');
  const [source, setSource] = useState<'AVAILABLE_FUND' | 'DIRECT_RECEIPT'>('AVAILABLE_FUND');
  const [branchId, setBranchId] = useState('');
  const [accountId, setAccountId] = useState('');
  const [amount, setAmount] = useState('');
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
      return { accounts: accounts.filter((item) => item.is_active), branches };
    }, retry: false,
  });
  const mutation = useMutation({
    mutationFn: () => phase5Api.recordInvestorExitLossApplication(companyId, userId, investorId, position.exit_request_id, {
      loss_result_id: lossResultId, branch_id: branchId, ...(source === 'DIRECT_RECEIPT' ? { account_id: accountId } : {}),
      source, amount, effective_at: new Date().toISOString(), expected_source_version: position.source_version, reason: reason.trim(),
    }),
    onSuccess: async () => {
      await onSaved();
      if (source === 'DIRECT_RECEIPT') await client.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) });
      await client.invalidateQueries({ queryKey: ['companies', userId, companyId, 'phase5', 'fund-credits'] });
      await client.invalidateQueries({ queryKey: ['companies', userId, companyId, 'phase5', 'fund-summary'] });
    },
  });
  const control = 'h-9 min-w-0 rounded-lg border border-gray-200 bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950';
  const currentLoss = position.confirmed_losses.find((item) => item.loss_result_id === lossResultId);
  return <form aria-label="Exit residual Loss application" className="mt-2 rounded-lg border border-gray-200 p-2.5 dark:border-zinc-700"
    onSubmit={(event) => { event.preventDefault(); if (!mutation.isPending) mutation.mutate(); }}>
    <p className="mb-2 text-[11px] font-bold">Apply confirmed Investor Loss · outstanding {currentLoss?.amount ?? '—'}</p>
    {options.isPending ? <p role="status" className="text-xs">Loading payment options…</p> : options.isError ?
      <p role="alert" className="text-xs text-red-700">Could not load payment options. <button type="button" onClick={() => void options.refetch()}>Retry</button></p> :
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <select aria-label="Exit Loss source" className={control} value={source} onChange={(event) => setSource(event.target.value as typeof source)}>
          <option value="AVAILABLE_FUND">Apply Available Fund</option><option value="DIRECT_RECEIPT">Record actual Investor receipt</option>
        </select>
        <select aria-label="Exit Loss Vehicle" className={control} value={lossResultId} onChange={(event) => setLossResultId(event.target.value)} required>
          {position.confirmed_losses.map((item) => <option key={item.loss_result_id} value={item.loss_result_id}>Vehicle {item.label} · {item.amount}</option>)}
        </select>
        <select aria-label="Exit Loss Branch" className={control} value={branchId} onChange={(event) => setBranchId(event.target.value)} required>
          <option value="">Select Branch</option>{options.data?.branches.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        {source === 'DIRECT_RECEIPT' && <select aria-label="Exit Loss Cash / Bank account" className={control} value={accountId} onChange={(event) => setAccountId(event.target.value)} required>
          <option value="">Select Cash / Bank</option>{options.data?.accounts.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>}
        <input aria-label="Exit Loss amount" className={control} inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} required placeholder="0.00" />
        <input aria-label="Exit Loss reason" className={control} value={reason} onChange={(event) => setReason(event.target.value)} required minLength={3} maxLength={500} placeholder="Accountant's case reason" />
      </div>}
    {mutation.error && <p role="alert" className="mt-2 text-xs text-red-700">{mutation.error instanceof Error ? mutation.error.message : 'Loss application failed.'}</p>}
    <div className="mt-2 flex justify-end"><button type="submit" disabled={!options.data || !currentLoss || !branchId || (source === 'DIRECT_RECEIPT' && !accountId) || !amount || reason.trim().length < 3 || mutation.isPending}
      className="h-8 rounded-lg bg-gray-900 px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">{mutation.isPending ? 'Saving…' : 'Record Loss application'}</button></div>
  </form>;
}
