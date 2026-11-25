import React from 'react';

export interface MonthlyPerformancePoint {
  label: string;
  income: number;
  expense: number;
}

interface PerformanceChartProps {
  points: MonthlyPerformancePoint[] | null;
  isLoading: boolean;
  hasError: boolean;
}

const formatAxisValue = (value: number) => {
  if (Math.abs(value) >= 100000) return `₹${(value / 100000).toFixed(Math.abs(value) >= 1000000 ? 0 : 1)}L`;
  if (Math.abs(value) >= 1000) return `₹${Math.round(value / 1000)}k`;
  return `₹${Math.round(value)}`;
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({ points, isLoading, hasError }) => {
  const valuesAvailable = points !== null && points.length === 8;
  const maximum = valuesAvailable ? Math.max(...points.flatMap((point) => [point.income, point.expense]), 0) : 0;
  const minimum = valuesAvailable ? Math.min(...points.flatMap((point) => [point.income, point.expense]), 0) : 0;
  const scaleMaximum = Math.max(1000, Math.ceil(maximum / 500) * 500);
  const scaleMinimum = Math.floor(minimum / 500) * 500;
  const chartTop = 10;
  const chartBottom = 160;
  const chartHeight = chartBottom - chartTop;
  const yFor = (value: number) => chartTop + (scaleMaximum - value) / (scaleMaximum - scaleMinimum) * chartHeight;
  const zeroY = yFor(0);
  const barWidth = 13;
  const barGap = 3;
  const groupSpacing = 38.5;
  const groupStartX = 35;

  return (
    <div className="dashboard-card-solid flex h-full flex-col justify-between rounded-[22px] p-4 sm:p-5">
      <div>
        <h3 className="text-sm font-bold leading-tight text-gray-950 dark:text-white sm:text-base">Monthly Income &amp; Expense</h3>
        <p className="mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">Recorded Accounting events</p>
      </div>

      <div className="mt-2 flex flex-col sm:mt-2.5">
        <div className="mb-1 flex flex-wrap items-center justify-between gap-x-2 gap-y-1 sm:mb-1.5">
          <span className="whitespace-nowrap text-[11px] font-bold tracking-tight text-gray-800 dark:text-gray-200">Income and Expense</span>
          <div className="flex items-center gap-3 text-[10px] font-semibold">
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-[2px] bg-[var(--theme-primary)]" />Income</span>
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-[2px] bg-[#18181b] dark:bg-zinc-200" />Expense</span>
          </div>
        </div>

        <div className="w-full overflow-hidden">
          <svg className="h-[186px] w-full sm:h-[195px]" viewBox="0 0 350 185" preserveAspectRatio="none" role="img" aria-label="Monthly Accounting income and expense for the last eight months">
            <defs>
              <pattern id="monthlyIncomeStripe" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="6" stroke="#ffffff" strokeWidth="1.8" />
              </pattern>
            </defs>
            {[0, 1, 2, 3, 4, 5].map((step) => {
              const value = scaleMaximum - (scaleMaximum - scaleMinimum) * step / 5;
              const y = chartTop + step * (chartHeight / 5);
              return <g key={step}>
                <text x="27" y={y + 3} textAnchor="end" className="fill-gray-400 text-[9px] font-medium dark:fill-zinc-500">{formatAxisValue(value)}</text>
                <line x1="33" y1={y} x2="346" y2={y} stroke="#e5e7eb" strokeDasharray={step === 5 ? 'none' : '3 3'} className="dark:stroke-zinc-800" />
              </g>;
            })}
            {scaleMinimum < 0 && <line x1="33" y1={zeroY} x2="346" y2={zeroY} stroke="#9ca3af" />}
            {valuesAvailable && points.map((point, index) => {
              const x = groupStartX + index * groupSpacing;
              const incomeHeight = point.income !== 0 ? Math.max(2, Math.abs(yFor(point.income) - zeroY)) : 0;
              const expenseHeight = point.expense !== 0 ? Math.max(2, Math.abs(yFor(point.expense) - zeroY)) : 0;
              return <g key={`${point.label}-${index}`}>
                {incomeHeight > 0 && <>
                  <rect x={x} y={point.income > 0 ? zeroY - incomeHeight : zeroY} width={barWidth} height={incomeHeight} rx="3" fill="var(--theme-primary)" />
                  <rect x={x} y={point.income > 0 ? zeroY - incomeHeight : zeroY} width={barWidth} height={incomeHeight} rx="3" fill="url(#monthlyIncomeStripe)" />
                </>}
                {expenseHeight > 0 && <rect x={x + barWidth + barGap} y={point.expense > 0 ? zeroY - expenseHeight : zeroY} width={barWidth} height={expenseHeight} rx="3" fill="#18181b" className="dark:fill-zinc-200" />}
                <text x={x + (barWidth * 2 + barGap) / 2} y="178" textAnchor="middle" className="fill-gray-500 text-[9px] font-medium dark:fill-zinc-400">{point.label}</text>
              </g>;
            })}
          </svg>
          {!valuesAvailable && <p role="status" className="-mt-2 text-center text-[11px] text-gray-500 dark:text-gray-400">
            {isLoading ? 'Loading monthly Accounting data…' : hasError ? 'Monthly Accounting data unavailable' : 'Monthly Accounting data unavailable'}
          </p>}
        </div>
      </div>
    </div>
  );
};
