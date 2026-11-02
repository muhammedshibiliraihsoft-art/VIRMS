import React from 'react';

interface MonthlyPerformancePoint {
  month: string;
  profit: number;
  loss: number;
}

const performanceData: MonthlyPerformancePoint[] = [
  { month: 'Jan', profit: 26000, loss: 17500 },
  { month: 'Feb', profit: 21000, loss: 12500 },
  { month: 'Mar', profit: 11000, loss: 8000 },
  { month: 'Apr', profit: 0, loss: 10500 },
  { month: 'May', profit: 0, loss: 6000 },
  { month: 'Jun', profit: 0, loss: 3500 },
  { month: 'Jul', profit: 0, loss: 800 },
  { month: 'Aug', profit: 0, loss: 600 },
];

export const PerformanceChart: React.FC = () => {
  const maxVal = 50000;
  const chartHeight = 150;
  const baseY = 160;
  const barWidth = 14;
  const barGap = 2.5;
  const groupSpacing = 38.5;
  const groupStartX = 36;

  return (
    <div className="dashboard-card-solid rounded-[22px] p-4 sm:p-5 flex flex-col justify-between h-full">
      {/* Title & Subtitle */}
      <div>
        <h3 className="text-sm sm:text-base font-bold text-gray-950 dark:text-white leading-tight">
          Total Income
        </h3>
        <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
          View your income in a certain period of time
        </p>
      </div>

      {/* Chart Section (Subheader + SVG Canvas positioned higher and compact) */}
      <div className="flex flex-col mt-2 sm:mt-2.5">
        {/* Subheader & Legend */}
        <div className="flex items-center justify-between mb-1 sm:mb-1.5">
          <span className="text-[11px] font-bold text-gray-800 dark:text-gray-200 tracking-tight">
            Profit and Loss
          </span>
          <div className="flex items-center gap-3 text-[11px] font-semibold">
            {/* Profit Legend (Solid Theme Fill + White Diagonal Stripes) */}
            <div className="flex items-center gap-1.5">
              <svg width="12" height="12" className="shrink-0 overflow-visible">
                <defs>
                  <pattern
                    id="legendStripe"
                    patternUnits="userSpaceOnUse"
                    width="4"
                    height="4"
                    patternTransform="rotate(45)"
                  >
                    <line x1="0" y1="0" x2="0" y2="4" stroke="#ffffff" strokeWidth="1.5" />
                  </pattern>
                </defs>
                <rect width="12" height="12" rx="2.5" fill="var(--theme-primary)" />
                <rect width="12" height="12" rx="2.5" fill="url(#legendStripe)" />
              </svg>
              <span className="text-gray-600 dark:text-gray-300 text-[10px]">Profit</span>
            </div>

            {/* Loss Legend (Solid Dark) */}
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-[2.5px] bg-[#18181b] dark:bg-zinc-200 inline-block" />
              <span className="text-gray-600 dark:text-gray-300 text-[10px]">Loss</span>
            </div>
          </div>
        </div>

        {/* Bar Chart Canvas */}
        <div className="w-full overflow-hidden">
          <svg
            className="w-full h-[186px] sm:h-[195px] overflow-visible"
            viewBox="0 0 350 185"
            preserveAspectRatio="none"
          >
            <defs>
              <pattern
                id="profitStripePattern"
                patternUnits="userSpaceOnUse"
                width="6"
                height="6"
                patternTransform="rotate(45)"
              >
                <line
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="6"
                  stroke="#ffffff"
                  strokeWidth="1.8"
                />
              </pattern>
            </defs>

            {/* Dotted Grid lines and Right-Aligned Y-axis labels */}
            {[50, 40, 30, 20, 10, 0].map((val, idx) => {
              const y = (idx * chartHeight) / 5 + 10;
              return (
                <g key={val}>
                  <text
                    x="21"
                    y={y + 3}
                    textAnchor="end"
                    className="fill-gray-400 dark:fill-zinc-500 text-[9px] font-medium"
                  >
                    {val === 0 ? '0' : `${val}k`}
                  </text>
                  <line
                    x1="26"
                    y1={y}
                    x2="346"
                    y2={y}
                    stroke="#e5e7eb"
                    strokeDasharray={val === 0 ? 'none' : '3 3'}
                    className="dark:stroke-zinc-800"
                  />
                </g>
              );
            })}

            {/* Render Separate Side-by-Side Bars (Profit Left + Loss Right per Month) */}
            {performanceData.map((d, i) => {
              const groupX = groupStartX + i * groupSpacing;
              const profitX = groupX;
              const lossX = groupX + barWidth + barGap;

              // Profit Bar calculations
              const hasProfit = d.profit > 0;
              const profitHeight = hasProfit ? Math.max(3, (d.profit / maxVal) * chartHeight) : 0;
              const profitY = baseY - profitHeight;

              // Loss Bar calculations
              const isLossTiny = d.loss < 1000;
              const lossHeight = isLossTiny ? 2.5 : Math.max(3, (d.loss / maxVal) * chartHeight);
              const lossY = baseY - lossHeight;

              // Month Label Center (middle of the side-by-side pair)
              const labelCenterX = groupX + barWidth + barGap / 2;

              return (
                <g key={d.month} className="group cursor-pointer">
                  {/* 1. Profit Bar (Solid Theme Accent Fill + White Diagonal Hatch Overlay) */}
                  {hasProfit && (
                    <>
                      <rect
                        x={profitX}
                        y={profitY}
                        width={barWidth}
                        height={profitHeight}
                        rx="3.5"
                        fill="var(--theme-primary)"
                      />
                      <rect
                        x={profitX}
                        y={profitY}
                        width={barWidth}
                        height={profitHeight}
                        rx="3.5"
                        fill="url(#profitStripePattern)"
                      />
                    </>
                  )}

                  {/* 2. Separate Loss Bar (Solid Dark Neutral, Right) */}
                  <rect
                    x={lossX}
                    y={lossY}
                    width={barWidth}
                    height={lossHeight}
                    rx={isLossTiny ? 1.5 : 3.5}
                    fill="#18181b"
                    className="dark:fill-zinc-300 transition-colors"
                  />

                  {/* Month Label Centered Under the Pair */}
                  <text
                    x={labelCenterX}
                    y={baseY + 16}
                    textAnchor="middle"
                    className="fill-gray-400 dark:fill-zinc-500 text-[9px] font-medium"
                  >
                    {d.month}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </div>
  );
};
