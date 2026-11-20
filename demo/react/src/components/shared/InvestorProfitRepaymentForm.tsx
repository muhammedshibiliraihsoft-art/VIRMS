import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { accountingAccounts } from '../../api/accountingApi';
import { authApi } from '../../api/authApi';
import { InvestorProfitPosition, phase5Api } from '../../api/phase5Api';
import { queryKeys } from '../../api/queryKeys';

export function InvestorProfitRepaymentForm({ companyId, userId, investorId, position, onClose }: {
  companyId: string; userId: string; investorId: string; position: InvestorProfitPosition; onClose: () => void;
}) {
  const client = useQueryClient();
  const [branchId, setBranchId] = useState('');
  const [accountId, setAccountId] = useState('');
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const options = useQuery({
    queryKey: ['companies', userId, companyId, 'phase8', 'repayment-inputs'],
    queryFn: async ({ signal }) => {
      const [accounts, branches] = await Promise.all([
        accountingAccounts(companyId, signal),
        (async () => {
          let page = await authApi.phase5Branches(companyId, 1, signal);
          const result = [...page.results];
          for (let n = 2; page.next; n++) {
            page = await authApi.phase5Branches(companyId, n, signal);
            result.push(...page.results);
          }
          return result;
        })(),
      ]);
      return { accounts: accounts.filter((account) => account.is_active), branches };
    },
    retry: false,
  });
  const mutation = useMutation({
    mutationFn: () => phase5Api.receiveInvestorProfitRepayment(companyId, userId, investorId, position.id, {
      branch_id: branchId, account_id: accountId, amount, reason: reason.trim(),
      expected_source_version: position.source_version,
    }),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: queryKeys.phase5.investorProfitPeriodProjection(userId, companyId, investorId) }),
        client.invalidateQueries({ queryKey: queryKeys.accountingBase(userId, companyId) }),
      ]);
      onClose();
    },
  });
  const control = 'h-9 min-w-0 rounded-lg border border-gray-200 bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950';
  return <form aria-label="Investor repayment" className="mb-3 rounded-xl border border-gray-200 p-3 dark:border-zinc-700"
    onSubmit={(event) => { event.preventDefault(); if (!mutation.isPending) mutation.mutate(); }}>
    <p className="mb-2 text-xs font-bold">Record actual Investor repayment · remaining {position.amount}</p>
    {options.isPending ? <p role="status" className="text-xs">Loading payment accounts and Branches…</p> : options.isError ?
      <p role="alert" className="text-xs text-red-700">Could not load repayment options. <button type="button" onClick={() => void options.refetch()}>Retry</button></p> :
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <select aria-label="Repayment Branch" className={control} value={branchId} onChange={(e) => setBranchId(e.target.value)} required>
          <option value="">Select Branch</option>{options.data?.branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
        </select>
        <select aria-label="Repayment Cash / Bank account" className={control} value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
          <option value="">Select Cash / Bank</option>{options.data?.accounts.map((account) => <option key={account.id} value={account.id}>{account.label}</option>)}
        </select>
        <input aria-label="Actual repayment amount" className={control} inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} required placeholder="0.00" />
        <input aria-label="Repayment reason" className={control} value={reason} onChange={(e) => setReason(e.target.value)} minLength={3} maxLength={500} required placeholder="Reason" />
      </div>}
    {mutation.error && <p role="alert" className="mt-2 text-xs text-red-700">{mutation.error instanceof Error ? mutation.error.message : 'Repayment failed.'}</p>}
    <div className="mt-2 flex justify-end gap-2">
      <button type="button" disabled={mutation.isPending} onClick={onClose} className="h-8 px-2 text-xs">Cancel</button>
      <button type="submit" disabled={!options.data || !branchId || !accountId || !amount || reason.trim().length < 3 || mutation.isPending}
        className="h-8 rounded-lg bg-gray-900 px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">Record receipt</button>
    </div>
  </form>;
}
