import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FutureProfitAdjustmentTarget, InvestorProfitPosition, phase5Api } from '../../api/phase5Api';
import { queryKeys } from '../../api/queryKeys';

export function InvestorProfitFutureAdjustmentForm({ companyId, userId, investorId, position, targets, onClose }: {
  companyId: string; userId: string; investorId: string; position: InvestorProfitPosition;
  targets: FutureProfitAdjustmentTarget[]; onClose: () => void;
}) {
  const client = useQueryClient();
  const [resultId, setResultId] = useState('');
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const selected = targets.find((target) => target.profit_result_id === resultId);
  const mutation = useMutation({
    mutationFn: () => {
      if (!selected) throw new Error('Select current future Profit.');
      return phase5Api.adjustInvestorRecoverableAgainstProfit(companyId, userId, investorId, position.id, {
        profit_position_id: selected.profit_position_id, profit_result_id: selected.profit_result_id,
        expected_source_version: position.source_version, expected_profit_source_version: selected.source_version,
        amount, reason: reason.trim(),
      });
    },
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: queryKeys.phase5.investorProfitPeriodProjection(userId, companyId, investorId) }),
        client.invalidateQueries({ queryKey: ['companies', userId, companyId, 'phase5', 'vehicle-financial-position'] }),
      ]);
      onClose();
    },
  });
  const control = 'h-9 min-w-0 rounded-lg border border-gray-200 bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-950';
  return <form aria-label="Future Profit adjustment" className="mb-3 rounded-xl border border-gray-200 p-3 dark:border-zinc-700"
    onSubmit={(event) => { event.preventDefault(); if (!mutation.isPending) mutation.mutate(); }}>
    <p className="mb-2 text-xs font-bold">Confirm future Profit adjustment · recoverable {position.amount}</p>
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
      <select aria-label="Future Profit source" className={control} value={resultId} onChange={(e) => setResultId(e.target.value)} required>
        <option value="">Select future Profit</option>
        {targets.map((target) => <option key={target.profit_result_id} value={target.profit_result_id}>{target.label} · available {target.amount}</option>)}
      </select>
      <input aria-label="Future adjustment amount" className={control} inputMode="decimal" value={amount}
        onChange={(e) => setAmount(e.target.value)} placeholder="0.00" required />
      <input aria-label="Future adjustment reason" className={control} value={reason}
        onChange={(e) => setReason(e.target.value)} placeholder="Reason" required minLength={3} maxLength={500} />
    </div>
    {!targets.length && <p role="status" className="mt-2 text-xs">No confirmed future Profit is available.</p>}
    {mutation.error && <p role="alert" className="mt-2 text-xs text-red-700">{mutation.error instanceof Error ? mutation.error.message : 'Adjustment failed.'}</p>}
    <div className="mt-2 flex justify-end gap-2">
      <button type="button" disabled={mutation.isPending} onClick={onClose} className="h-8 px-2 text-xs">Cancel</button>
      <button type="submit" disabled={!selected || !amount || reason.trim().length < 3 || mutation.isPending}
        className="h-8 rounded-lg bg-gray-900 px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">Confirm adjustment</button>
    </div>
  </form>;
}
