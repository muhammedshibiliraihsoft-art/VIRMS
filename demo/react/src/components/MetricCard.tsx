import React from 'react';
import { Info, Lock, Layers } from 'lucide-react';

interface MetricGridProps {
  vehicleCount: number | null;
  soldVehicleCount: number | null;
  buyerReceivable: number | null;
  openJobsCount: number | null;
  vehiclesLoading: boolean;
  vehiclesError: boolean;
  garageLoading: boolean;
  garageError: boolean;
}

export const MetricGrid: React.FC<MetricGridProps> = ({
  vehicleCount,
  soldVehicleCount,
  buyerReceivable,
  openJobsCount,
  vehiclesLoading,
  vehiclesError,
  garageLoading,
  garageError,
}) => {
  const formatCompact = (val: number) => {
    if (val >= 100000) {
      return '₹' + (val / 100000).toFixed(2) + 'L';
    }
    return '₹' + val.toLocaleString('en-IN');
  };
  const formatCount = (value: number | null, isLoading: boolean, hasError: boolean) => isLoading ? '…' : hasError || value === null ? 'Unavailable' : value.toLocaleString('en-IN');
  const formatMoney = (value: number | null, isLoading: boolean, hasError: boolean) => isLoading ? '…' : hasError || value === null ? 'Unavailable' : formatCompact(value);

  return (
    <div className="grid grid-cols-2 grid-rows-2 gap-2.5 sm:gap-3 h-full">
      {/* Preserve the original accent card for the authorized vehicle count. */}
      <div className="dashboard-card-orange text-white rounded-[20px] p-3.5 sm:p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-white/95">
            Total Vehicles
          </span>
          <div className="w-4 h-4 rounded-full border border-white/40 flex items-center justify-center text-white/95">
            <Info className="w-2.5 h-2.5" />
          </div>
        </div>

        <div className="my-auto py-0.5">
          <div className="text-2xl sm:text-[28px] font-extrabold tracking-tight">
            {formatCount(vehicleCount, vehiclesLoading, vehiclesError)}
          </div>
        </div>

        <span className="text-[10px] text-white/90 font-medium">Authorized scope</span>
      </div>

      {/* The API returns the total authorized job count, not only open jobs. */}
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
            {formatCount(openJobsCount, garageLoading, garageError)}
          </div>
        </div>

        <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">Garage · open</span>
      </div>

      {/* Buyer receivable remains separate from actual Cash/Bank balance. */}
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
            {formatMoney(buyerReceivable, vehiclesLoading, vehiclesError)}
          </div>
        </div>

        <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">Unpaid buyer balance</span>
      </div>

      {/* 4. Sold vehicle count keeps the final dashboard metric slot data-backed. */}
      <div className="dashboard-card-solid rounded-[20px] p-3.5 sm:p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">Sold Vehicles</span>
          <div className="w-4 h-4 rounded-full bg-white dark:bg-zinc-800 border border-[#f0eae4] dark:border-zinc-700 flex items-center justify-center text-gray-400 dark:text-gray-300">
            <Layers className="w-2.5 h-2.5" />
          </div>
        </div>
        <div className="my-auto py-0.5">
          <div className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight truncate">
            {formatCount(soldVehicleCount, vehiclesLoading, vehiclesError)}
          </div>
        </div>
        <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">Authorized scope</span>
      </div>
    </div>
  );
};
