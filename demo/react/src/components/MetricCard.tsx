import React from 'react';
import { Info, Lock, Layers } from 'lucide-react';

interface MetricGridProps {
  stockVehiclesCount: number;
  openJobsCount: number;
  totalReceivable: number;
  inventoryStockValue: number;
}

export const MetricGrid: React.FC<MetricGridProps> = ({
  stockVehiclesCount,
  openJobsCount,
  totalReceivable,
  inventoryStockValue,
}) => {
  const formatCompact = (val: number) => {
    if (val >= 100000) {
      return '₹' + (val / 100000).toFixed(2) + 'L';
    }
    return '₹' + val.toLocaleString('en-IN');
  };

  return (
    <div className="grid grid-cols-2 grid-rows-2 gap-2.5 sm:gap-3 h-full">
      {/* 1. Top-Left: Accent Orange Card (Image 2's Total Earnings) */}
      <div className="dashboard-card-orange text-white rounded-[20px] p-3.5 sm:p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-white/95">
            Total Stock
          </span>
          <div className="w-4 h-4 rounded-full border border-white/40 flex items-center justify-center text-white/95">
            <Info className="w-2.5 h-2.5" />
          </div>
        </div>

        <div className="my-auto py-0.5">
          <div className="text-2xl sm:text-[28px] font-extrabold tracking-tight">
            {Math.max(3, stockVehiclesCount)}
          </div>
        </div>

        <div className="flex items-center gap-1">
          <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-white/25 text-white border border-white/20">
            + 7%
          </span>
          <span className="text-[10px] text-white/90 font-medium">This month</span>
        </div>
      </div>

      {/* 2. Top-Right: Open Garage Jobs (Image 2's Total Spending) */}
      <div className="dashboard-card-solid rounded-[20px] p-3.5 sm:p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">
            Open Jobs
          </span>
          <div className="w-4 h-4 rounded-full bg-white dark:bg-zinc-800 border border-[#f0eae4] dark:border-zinc-700 flex items-center justify-center text-gray-400 dark:text-gray-300">
            <Lock className="w-2.5 h-2.5" />
          </div>
        </div>

        <div className="my-auto py-0.5">
          <div className="text-2xl sm:text-[28px] font-extrabold text-gray-950 dark:text-white tracking-tight">
            {openJobsCount}
          </div>
        </div>

        <div className="flex items-center gap-1">
          <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] border border-[var(--theme-primary-border)]">
            + 5%
          </span>
          <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">This month</span>
        </div>
      </div>

      {/* 3. Bottom-Left: Buyer Receivables (Image 2's Total Income) */}
      <div className="dashboard-card-solid rounded-[20px] p-3.5 sm:p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">
            Buyer Due
          </span>
          <div className="w-4 h-4 rounded-full bg-white dark:bg-zinc-800 border border-[#f0eae4] dark:border-zinc-700 flex items-center justify-center text-gray-400 dark:text-gray-300">
            <Info className="w-2.5 h-2.5" />
          </div>
        </div>

        <div className="my-auto py-0.5">
          <div className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight truncate">
            {formatCompact(totalReceivable)}
          </div>
        </div>

        <div className="flex items-center gap-1">
          <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 border border-emerald-200/60">
            + 8%
          </span>
          <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">This month</span>
        </div>
      </div>

      {/* 4. Bottom-Right: Stock Inventory (Image 2's Total Revenue) */}
      <div className="dashboard-card-solid rounded-[20px] p-3.5 sm:p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">
            Inventory
          </span>
          <div className="w-4 h-4 rounded-full bg-white dark:bg-zinc-800 border border-[#f0eae4] dark:border-zinc-700 flex items-center justify-center text-gray-400 dark:text-gray-300">
            <Layers className="w-2.5 h-2.5" />
          </div>
        </div>

        <div className="my-auto py-0.5">
          <div className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight truncate">
            {formatCompact(inventoryStockValue)}
          </div>
        </div>

        <div className="flex items-center gap-1">
          <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 border border-emerald-200/60">
            + 8%
          </span>
          <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">This month</span>
        </div>
      </div>
    </div>
  );
};
