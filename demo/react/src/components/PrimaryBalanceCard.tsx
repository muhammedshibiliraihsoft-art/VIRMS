import React from 'react';
import { ArrowLeftRight, Plus } from 'lucide-react';
import type { AccountingAccount } from '../api/accountingApi';
import { useCanPresentBusinessWriteActions } from '../auth/RolePresentationContext';

interface PrimaryBalanceCardProps {
  accounts?: AccountingAccount[];
  isLoading: boolean;
  hasError: boolean;
  onRecordReceipt: () => void;
  onNewSale: () => void;
}

export const PrimaryBalanceCard: React.FC<PrimaryBalanceCardProps> = ({
  accounts,
  isLoading,
  hasError,
  onRecordReceipt,
  onNewSale,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const formatCurrency = (val: number) =>
    '₹' + val.toLocaleString('en-IN', { maximumFractionDigits: 0 });
  const cashBankAccounts = hasError ? [] : accounts?.filter((account) => account.account_type === 'CASH' || account.account_type === 'BANK') ?? [];
  const balanceUnavailable = !hasError && !isLoading && cashBankAccounts.some((account) => account.current_balance === undefined);
  const totalBalance = cashBankAccounts.reduce((total, account) => total + Number(account.current_balance ?? 0), 0);
  const formatValue = (value?: string) => value === undefined ? 'Unavailable' : formatCurrency(Number(value));

  return (
    <div className="dashboard-card-solid rounded-[22px] p-4 sm:p-5 flex flex-col justify-between h-full">
      {/* Top Section: Title & Currency */}
      <div>
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">
            Total Balance
          </span>
          <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white dark:bg-zinc-800 border border-[#f0eae4] dark:border-zinc-700 text-[10px] font-bold text-gray-700 dark:text-gray-200 shadow-2xs">
            <span>🇮🇳</span>
            <span>INR ₹</span>
          </div>
        </div>

      {/* Current persisted fund availability */}
        <div className="mt-2">
          <div className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
            {isLoading ? 'Loading…' : hasError || balanceUnavailable ? 'Unavailable' : formatCurrency(totalBalance)}
          </div>
          <p className="text-[11px] text-gray-400 dark:text-gray-500 font-medium mt-1.5">Authorized scope · INR</p>
        </div>

        {/* Action Buttons */}
        {canPresentWriteActions && (
          <div className="grid grid-cols-2 gap-2.5 mt-4">
            <button
              onClick={onRecordReceipt}
              className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-full bg-[#18181b] hover:bg-black text-white font-bold text-[11px] shadow-xs transition cursor-pointer active:scale-[0.98]"
            >
              <ArrowLeftRight className="w-3 h-3" />
              <span className="truncate">Record Receipt</span>
            </button>
            <button
              onClick={onNewSale}
              className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/90 dark:border-zinc-700 text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-zinc-700 font-bold text-[11px] shadow-2xs transition cursor-pointer active:scale-[0.98]"
            >
              <Plus className="w-3 h-3 text-gray-600 dark:text-gray-400" />
              <span className="truncate">New Sale</span>
            </button>
          </div>
        )}
      </div>

        {/* Preserve the original three nested slots with actual Cash/Bank accounts. */}
      <div className="mt-4 pt-3 border-t border-[#f0eae4] dark:border-zinc-750">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[11px] font-bold text-gray-900 dark:text-white">
            Cash / Bank Accounts{' '}
            <span className="font-normal text-gray-400 dark:text-gray-500 text-[10px]">
              | Total {hasError ? 'Unavailable' : isLoading ? '…' : cashBankAccounts.length}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-1.5">
          {cashBankAccounts.slice(0, 3).map((account, index) => (
            <div key={account.id} className="dashboard-nested-card rounded-xl p-2">
              <div className="flex items-center gap-1 min-w-0 mb-1">
                  <div className={`w-3 h-3 rounded-full flex items-center justify-center text-[7px] font-bold text-white shrink-0 ${index === 0 ? 'bg-[var(--theme-primary)]' : index === 1 ? 'bg-blue-600' : 'bg-emerald-600'}`}>
                  {account.account_type === 'BANK' ? 'B' : 'C'}
                </div>
                <span className="text-[9px] font-bold text-gray-800 dark:text-gray-200 truncate">{account.label}</span>
              </div>
              <div className="text-[10px] sm:text-[11px] font-extrabold text-gray-950 dark:text-white mt-0.5 truncate">
                {isLoading ? 'Loading…' : hasError || balanceUnavailable ? 'Unavailable' : formatValue(account.current_balance)}
              </div>
              <div className="text-[8px] text-gray-400 dark:text-gray-500 truncate">{account.account_type === 'BANK' ? 'Bank' : 'Cash'}</div>
            </div>
          ))}
          {cashBankAccounts.length === 0 && (
            <p className="col-span-3 py-3 text-center text-[9px] text-gray-400 dark:text-gray-500">
              {isLoading ? 'Loading accounts…' : hasError ? 'Accounts unavailable' : 'No Cash/Bank accounts'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
