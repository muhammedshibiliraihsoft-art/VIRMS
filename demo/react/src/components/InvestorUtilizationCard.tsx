import React from 'react';

interface InvestorUtilizationCardProps {
  totalPrincipal: number;
  totalUsed: number;
}

export const InvestorUtilizationCard: React.FC<InvestorUtilizationCardProps> = ({
  totalPrincipal,
  totalUsed,
}) => {
  const formatCurrency = (val: number) =>
    '₹' + val.toLocaleString('en-IN', { maximumFractionDigits: 0 });

  return (
    <div className="dashboard-card-solid rounded-[22px] p-4 sm:p-5 flex flex-col justify-between h-full min-h-[135px]">
      <div>
        <h3 className="text-[11px] font-bold text-gray-950 dark:text-white">
          Monthly Spending Limit
        </h3>

        {/* Progress bar matching Image 2 */}
        <div className="relative w-full h-2.5 rounded-full overflow-hidden bg-gray-200 dark:bg-zinc-800 flex items-center p-0.5 mt-2.5 sm:mt-3">
          {/* Theme active portion */}
          <div
            className="h-full rounded-full bg-[var(--theme-primary)]"
            style={{ width: '24%' }}
          />

          {/* Striped unfilled pattern */}
          <div className="flex-1 h-full rounded-full bg-[repeating-linear-gradient(45deg,#e2e8f0,#e2e8f0_2px,#f1f5f9_2px,#f1f5f9_6px)]" />
        </div>
      </div>

      <div className="flex items-center justify-between pt-2.5 text-xs font-bold text-gray-900 dark:text-gray-100">
        <div>
          <span className="text-xs font-extrabold text-gray-950 dark:text-white">
            {formatCurrency(totalUsed)}
          </span>{' '}
          <span className="text-gray-400 dark:text-gray-500 font-normal text-[10px]">
            used out of
          </span>
        </div>
        <div className="text-xs font-extrabold text-gray-950 dark:text-white">
          {formatCurrency(totalPrincipal)}
        </div>
      </div>
    </div>
  );
};
