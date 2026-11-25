import React from 'react';

interface InvestorUtilizationCardProps {
  totalUsed?: number;
  availableAmount?: number;
  reservedAmount?: number;
  isLoading?: boolean;
  hasError?: boolean;
}

export const InvestorUtilizationCard: React.FC<InvestorUtilizationCardProps> = ({
  totalUsed,
  availableAmount,
  reservedAmount,
  isLoading = false,
  hasError = false,
}) => {
  const formatCurrency = (val: number) =>
    '₹' + val.toLocaleString('en-IN', { maximumFractionDigits: 0 });

  const hasValues = !isLoading && !hasError && totalUsed !== undefined && availableAmount !== undefined && reservedAmount !== undefined;
  const fundPositionTotal = hasValues ? totalUsed + availableAmount + reservedAmount : 0;
  const percentage = hasValues && fundPositionTotal > 0
    ? Math.min(100, Math.max(0, (totalUsed / fundPositionTotal) * 100))
    : 0;
  const valueText = (value?: number) => isLoading
    ? 'Loading…'
    : hasError || value === undefined
      ? 'Unavailable'
      : formatCurrency(value);

  return (
    <div className="dashboard-card-solid rounded-[22px] p-4 sm:p-5 flex flex-col justify-between h-full min-h-[135px]">
      <div>
        <h3 className="text-[11px] font-bold text-gray-950 dark:text-white">
          Investor Fund Position
        </h3>

        {/* Progress reflects the authorized Fund summary; no demo percentage. */}
        <div className="relative w-full h-2.5 rounded-full overflow-hidden bg-gray-200 dark:bg-zinc-800 flex items-center p-0.5 mt-2.5 sm:mt-3">
          {/* Theme active portion */}
          <div
            className="h-full rounded-full bg-[var(--theme-primary)]"
            style={{ width: `${percentage}%` }}
          />

          {/* Striped unfilled pattern */}
          <div className="flex-1 h-full rounded-full bg-[repeating-linear-gradient(45deg,#e2e8f0,#e2e8f0_2px,#f1f5f9_2px,#f1f5f9_6px)]" />
        </div>
      </div>

      <div className="flex items-center justify-between pt-2.5 text-xs font-bold text-gray-900 dark:text-gray-100">
        <div>
          <span className="text-xs font-extrabold text-gray-950 dark:text-white">
            {valueText(totalUsed)}
          </span>{' '}
          <span className="text-gray-400 dark:text-gray-500 font-normal text-[10px]">
            used
          </span>
        </div>
        <div className="text-xs font-extrabold text-gray-950 dark:text-white">
          {valueText(availableAmount)}
        </div>
      </div>
    </div>
  );
};
