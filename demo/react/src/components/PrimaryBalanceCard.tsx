import React from 'react';
import { ArrowLeftRight, Plus, MoreVertical } from 'lucide-react';
import { Investor } from '../types';

interface PrimaryBalanceCardProps {
  totalReceivable: number;
  investors: Investor[];
  onRecordReceipt: () => void;
  onNewSale: () => void;
}

export const PrimaryBalanceCard: React.FC<PrimaryBalanceCardProps> = ({
  totalReceivable,
  investors,
  onRecordReceipt,
  onNewSale,
}) => {
  const formatCurrency = (val: number) =>
    '₹' + val.toLocaleString('en-IN', { maximumFractionDigits: 0 });

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

        {/* Large Value & Trend */}
        <div className="mt-2">
          <div className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
            {formatCurrency(totalReceivable)}
          </div>
          <div className="flex items-center gap-1.5 mt-1.5">
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/60">
              <span className="text-[9px]">↗</span> + 5%
            </span>
            <span className="text-[11px] text-gray-400 dark:text-gray-500 font-medium">
              than last month
            </span>
          </div>
        </div>

        {/* Action Buttons */}
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
      </div>

      {/* Bottom Section: Mini Investor Wallets */}
      <div className="mt-4 pt-3 border-t border-[#f0eae4] dark:border-zinc-750">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[11px] font-bold text-gray-900 dark:text-white">
            Wallets{' '}
            <span className="font-normal text-gray-400 dark:text-gray-500 text-[10px]">
              | Total {investors.length}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-1.5">
          {investors.slice(0, 3).map((inv, idx) => (
            <div
              key={inv.id}
              className="dashboard-nested-card rounded-xl p-2 hover:border-[#ded5cb] dark:hover:border-zinc-600 transition"
            >
              <div className="flex items-center justify-between mb-0.5">
                <div className="flex items-center gap-1 min-w-0">
                  <div
                    className={`w-3 h-3 rounded-full flex items-center justify-center text-[7px] font-bold text-white shrink-0 ${
                      idx === 0
                        ? 'bg-[var(--theme-primary)]'
                        : idx === 1
                        ? 'bg-blue-600'
                        : 'bg-emerald-600'
                    }`}
                  >
                    {inv.name.charAt(0)}
                  </div>
                  <span className="text-[10px] font-bold text-gray-800 dark:text-gray-200 truncate">
                    {inv.name.split(' ')[0]}
                  </span>
                </div>
                <MoreVertical className="w-2.5 h-2.5 text-gray-300 dark:text-gray-600 shrink-0" />
              </div>
              <div className="text-[10px] sm:text-[11px] font-extrabold text-gray-950 dark:text-white mt-0.5 truncate">
                {formatCurrency(inv.available ?? inv.principal)}
              </div>
              <div className="text-[8px] text-gray-400 dark:text-gray-500 truncate">
                Available
              </div>
              <div className="mt-0.5">
                <span className="inline-block text-[8px] font-bold text-emerald-600 dark:text-emerald-400">
                  Active
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
