import React, { useState } from 'react';
import {
  TrendingUp,
  Award,
  Clock,
  ArrowUpRight,
  Filter,
  CheckCircle2,
  Users,
  PieChart,
  BarChart,
  ChevronDown,
} from 'lucide-react';
import { Data } from '../../types';
import { formatCurrency, formatCompact } from '../../utils/formatters';

interface DashboardAnalyticsViewProps {
  data: Data;
  selectedGarage: string;
  onSelectRoute: (routeKey: string) => void;
}

export const DashboardAnalyticsView: React.FC<DashboardAnalyticsViewProps> = ({
  data,
  selectedGarage,
  onSelectRoute,
}) => {
  const [timeframe, setTimeframe] = useState<'month' | 'quarter' | 'year'>('month');

  const { vehicles, jobs, sales, garages } = data;

  const filteredJobs =
    selectedGarage === 'all'
      ? jobs
      : jobs.filter((j) => j.garageId === selectedGarage);

  const totalJobCharges = filteredJobs.reduce((sum, j) => sum + (j.charge || 0), 0);
  const totalSalesRevenue = sales.reduce((sum, s) => sum + (s.price || 0), 0);
  const totalRevenue = totalSalesRevenue + totalJobCharges;

  // Technicians / Service Advisors (Reference 2 Inspiration)
  const topAdvisors = [
    { name: 'Kamal David', role: 'Senior Diagnostic Tech', jobs: 18, revenue: 384000, progress: 88 },
    { name: 'Aisha Khan', role: 'Electrical Specialist', jobs: 14, revenue: 295000, progress: 72 },
    { name: 'Leo Martins', role: 'Chassis & Suspension Tech', jobs: 11, revenue: 198000, progress: 58 },
    { name: 'Sanjay Rawat', role: 'Paint & Body Lead', jobs: 9, revenue: 142000, progress: 45 },
  ];

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* 1. Top Header Row: Section Title + Subtitle + Timeframe Selector (Reference 2 Top Header) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-0.5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg sm:text-xl font-extrabold text-gray-950 dark:text-white tracking-tight">
              Operational & Revenue Analytics
            </h2>
            <span className="w-4 h-4 rounded-full bg-[var(--theme-primary)] text-white text-[9px] font-bold flex items-center justify-center">
              i
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            Comparative performance, workshop execution funnel, and technician throughput.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center p-0.5 rounded-full bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10 text-xs font-bold">
            {(['month', 'quarter', 'year'] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1 rounded-full uppercase text-[10px] tracking-wider transition cursor-pointer ${
                  timeframe === tf
                    ? 'bg-white dark:bg-zinc-800 text-gray-950 dark:text-white shadow-2xs font-extrabold'
                    : 'text-gray-500 hover:text-black dark:hover:text-white'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Top KPI Row: 4 Metric Cards (Card 1 Theme Primary Accent, Reference 2 Top Row) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Card 1: Theme Accent Card */}
        <div className="dashboard-card-orange rounded-[22px] p-4 text-white flex flex-col justify-between shadow-xs select-none">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-white/90">Total Revenue</span>
            <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded-full bg-white/20 text-white">
              + 8.1%
            </span>
          </div>
          <div className="my-2">
            <div className="text-2xl sm:text-[28px] font-extrabold tracking-tight">
              {formatCompact(totalRevenue)}
            </div>
            <div className="text-[10px] text-white/80 mt-0.5 font-medium">
              Realized collections & invoices
            </div>
          </div>
          <div className="w-full bg-white/20 h-1.5 rounded-full overflow-hidden">
            <div className="bg-white h-full rounded-full" style={{ width: '78%' }} />
          </div>
        </div>

        {/* Card 2: Workshop Efficiency */}
        <div className="dashboard-card-solid rounded-[22px] p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">
              Throughput Efficiency
            </span>
            <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              + 12%
            </span>
          </div>
          <div className="my-2">
            <div className="text-2xl sm:text-[28px] font-extrabold text-gray-950 dark:text-white tracking-tight">
              83.3%
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5 font-medium">
              Completed jobs within estimated hours
            </div>
          </div>
          <div className="w-full bg-black/5 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-[var(--theme-primary)] h-full rounded-full" style={{ width: '83%' }} />
          </div>
        </div>

        {/* Card 3: Gross Margin */}
        <div className="dashboard-card-solid rounded-[22px] p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">
              Sales Margin
            </span>
            <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              + 3.4%
            </span>
          </div>
          <div className="my-2">
            <div className="text-2xl sm:text-[28px] font-extrabold text-gray-950 dark:text-white tracking-tight">
              24.5%
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5 font-medium">
              Average net margin on closed vehicles
            </div>
          </div>
          <div className="w-full bg-black/5 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: '65%' }} />
          </div>
        </div>

        {/* Card 4: Avg Repair Ticket Size */}
        <div className="dashboard-card-solid rounded-[22px] p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-gray-500 dark:text-gray-400">
              Avg Ticket Size
            </span>
            <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              + 4.2%
            </span>
          </div>
          <div className="my-2">
            <div className="text-2xl sm:text-[28px] font-extrabold text-gray-950 dark:text-white tracking-tight">
              ₹18,500
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5 font-medium">
              Average service invoice value
            </div>
          </div>
          <div className="w-full bg-black/5 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-blue-500 h-full rounded-full" style={{ width: '70%' }} />
          </div>
        </div>
      </div>

      {/* 3. Middle Row: 2 Comparative Large Charts (Reference 2 Middle Area) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 items-stretch">
        {/* Chart 1: Revenue Spline Trend with Gradient Wash */}
        <div className="dashboard-card-solid rounded-[24px] p-4 sm:p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="text-xs sm:text-sm font-bold text-gray-950 dark:text-white tracking-tight">
                Revenue Realization Curve
              </span>
              <p className="text-[10px] text-gray-400">Realized vehicle and service collections</p>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-bold text-gray-600 dark:text-gray-300">
              <span className="w-2.5 h-2.5 rounded-full bg-[var(--theme-primary)]" />
              <span>Realized (₹)</span>
            </div>
          </div>

          {/* SVG Smooth Curve Area Chart */}
          <div className="w-full">
            <svg viewBox="0 0 450 160" className="w-full h-44 overflow-visible">
              <defs>
                <linearGradient id="revenueSplineGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--theme-primary)" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="var(--theme-primary)" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Gridlines */}
              {[20, 15, 10, 5, 0].map((v, i) => (
                <g key={v}>
                  <text x="18" y={i * 30 + 15} textAnchor="end" className="fill-gray-400 text-[8px] font-medium">
                    {v === 0 ? '0' : `${v}L`}
                  </text>
                  <line
                    x1="24"
                    y1={i * 30 + 12}
                    x2="445"
                    y2={i * 30 + 12}
                    stroke="#e5e7eb"
                    strokeDasharray={v === 0 ? 'none' : '2 2'}
                    className="dark:stroke-zinc-800"
                  />
                </g>
              ))}

              {/* Area under spline */}
              <path
                d="M 35 110 C 90 95, 130 120, 180 85 C 220 50, 240 40, 280 42 C 340 45, 380 90, 435 115 L 435 132 L 35 132 Z"
                fill="url(#revenueSplineGrad)"
              />

              {/* Main Spline Line */}
              <path
                d="M 35 110 C 90 95, 130 120, 180 85 C 220 50, 240 40, 280 42 C 340 45, 380 90, 435 115"
                fill="none"
                stroke="var(--theme-primary)"
                strokeWidth="2.8"
                strokeLinecap="round"
              />

              {/* Peak Point Tooltip (Reference 2 Callout) */}
              <line x1="260" y1="41" x2="260" y2="132" stroke="var(--theme-primary)" strokeWidth="1" strokeDasharray="2 2" />
              <circle cx="260" cy="41" r="5" fill="#ffffff" stroke="var(--theme-primary)" strokeWidth="2.5" />
              <rect x="230" y="10" width="60" height="22" rx="6" fill="#18181b" />
              <text x="260" y="24" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="bold">
                ₹6,45,000
              </text>

              {/* Dates */}
              {['Oct 5', 'Oct 9', 'Oct 13', 'Oct 17', 'Oct 21', 'Oct 25'].map((d, idx) => (
                <text key={d} x={45 + idx * 72} y="148" textAnchor="middle" className="fill-gray-400 text-[8px] font-medium">
                  {d}
                </text>
              ))}
            </svg>
          </div>
        </div>

        {/* Chart 2: Revenue vs Target Benchmark */}
        <div className="dashboard-card-solid rounded-[24px] p-4 sm:p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="text-xs sm:text-sm font-bold text-gray-950 dark:text-white tracking-tight">
                Revenue vs Monthly Target
              </span>
              <p className="text-[10px] text-gray-400">Actual pace versus allocated threshold</p>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-bold">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--theme-primary)]" />
                <span className="text-gray-600 dark:text-gray-300">Revenue</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-0.5 bg-[#18181b] dark:bg-zinc-200" />
                <span className="text-gray-600 dark:text-gray-300">Target Line</span>
              </div>
            </div>
          </div>

          {/* SVG Comparative Chart */}
          <div className="w-full">
            <svg viewBox="0 0 450 160" className="w-full h-44 overflow-visible">
              {/* Dotted Grid */}
              {[20, 15, 10, 5, 0].map((v, i) => (
                <g key={v}>
                  <text x="18" y={i * 30 + 15} textAnchor="end" className="fill-gray-400 text-[8px] font-medium">
                    {v === 0 ? '0' : `${v}L`}
                  </text>
                  <line
                    x1="24"
                    y1={i * 30 + 12}
                    x2="445"
                    y2={i * 30 + 12}
                    stroke="#e5e7eb"
                    strokeDasharray={v === 0 ? 'none' : '2 2'}
                    className="dark:stroke-zinc-800"
                  />
                </g>
              ))}

              {/* Bold Target Threshold Baseline */}
              <line x1="28" y1="72" x2="440" y2="72" stroke="#18181b" strokeWidth="1.8" className="dark:stroke-zinc-400" />

              {/* Actual Curve showing Variance */}
              <path
                d="M 35 78 C 80 82, 120 115, 170 120 C 210 125, 230 45, 270 42 C 320 40, 360 85, 435 90"
                fill="none"
                stroke="var(--theme-primary)"
                strokeWidth="2.8"
                strokeLinecap="round"
              />

              {/* Dates */}
              {['Oct 5', 'Oct 9', 'Oct 13', 'Oct 17', 'Oct 21', 'Oct 25'].map((d, idx) => (
                <text key={d} x={45 + idx * 72} y="148" textAnchor="middle" className="fill-gray-400 text-[8px] font-medium">
                  {d}
                </text>
              ))}
            </svg>
          </div>
        </div>
      </div>

      {/* 4. Bottom Row: 3 Analytical Breakdown Panels (Reference 2 Bottom Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-stretch">
        {/* Panel 1: Revenue Streams Donut Chart */}
        <div className="dashboard-card-solid rounded-[24px] p-4 sm:p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-gray-950 dark:text-white tracking-tight">
              Revenue Streams
            </span>
            <PieChart className="w-3.5 h-3.5 text-gray-400" />
          </div>

          <div className="flex items-center justify-center my-2 relative">
            <svg viewBox="0 0 100 100" className="w-28 h-28 transform -rotate-90">
              {/* Segment 1: Vehicle Sales (52%) */}
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="var(--theme-primary)"
                strokeWidth="12"
                strokeDasharray="124 238"
                strokeDashoffset="0"
              />
              {/* Segment 2: Garage Services (32%) */}
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="#18181b"
                strokeWidth="12"
                strokeDasharray="76 238"
                strokeDashoffset="-124"
                className="dark:stroke-zinc-300"
              />
              {/* Segment 3: Spare Parts (16%) */}
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="#9ca3af"
                strokeWidth="12"
                strokeDasharray="38 238"
                strokeDashoffset="-200"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-lg font-extrabold text-gray-950 dark:text-white leading-none">
                52%
              </span>
              <span className="text-[9px] text-gray-400 font-semibold mt-0.5">Vehicles</span>
            </div>
          </div>

          {/* Donut Legend */}
          <div className="space-y-1.5 pt-2 border-t border-gray-100 dark:border-zinc-800 text-[11px]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[var(--theme-primary)]" />
                <span className="text-gray-600 dark:text-gray-300">Vehicle Sales</span>
              </div>
              <span className="font-extrabold text-gray-900 dark:text-white">52%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#18181b] dark:bg-zinc-300" />
                <span className="text-gray-600 dark:text-gray-300">Workshop Services</span>
              </div>
              <span className="font-extrabold text-gray-900 dark:text-white">32%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-gray-400" />
                <span className="text-gray-600 dark:text-gray-300">Spare Parts & Stock</span>
              </div>
              <span className="font-extrabold text-gray-900 dark:text-white">16%</span>
            </div>
          </div>
        </div>

        {/* Panel 2: Job Execution Funnel */}
        <div className="dashboard-card-solid rounded-[24px] p-4 sm:p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-gray-950 dark:text-white tracking-tight">
              Job Execution Funnel
            </span>
            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              82% Conv.
            </span>
          </div>

          <div className="space-y-2 my-1">
            {[
              { stage: 'Intake / Booking', count: 12, pct: 100, barWidth: 'w-full' },
              { stage: 'Diagnostic Checked', count: 10, pct: 83, barWidth: 'w-[83%]' },
              { stage: 'Work in Progress', count: 8, pct: 66, barWidth: 'w-[66%]' },
              { stage: 'Quality Inspection', count: 5, pct: 41, barWidth: 'w-[41%]' },
              { stage: 'Invoice & Settled', count: 4, pct: 33, barWidth: 'w-[33%]' },
            ].map((s) => (
              <div key={s.stage} className="space-y-1">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-gray-600 dark:text-gray-300 font-medium">{s.stage}</span>
                  <span className="font-bold text-gray-900 dark:text-white">
                    {s.count} <span className="text-gray-400">({s.pct}%)</span>
                  </span>
                </div>
                <div className="w-full bg-black/5 dark:bg-white/10 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[var(--theme-primary)] transition-all"
                    style={{ width: `${s.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => onSelectRoute('Garage Jobs')}
            className="text-[10px] font-bold text-[var(--theme-primary)] hover:underline text-left pt-1 cursor-pointer"
          >
            Review Active Job Pipeline →
          </button>
        </div>

        {/* Panel 3: Top Service Advisors & Technicians Leaderboard */}
        <div className="dashboard-card-solid rounded-[24px] p-4 sm:p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-gray-950 dark:text-white tracking-tight">
              Top Service Advisors
            </span>
            <Award className="w-3.5 h-3.5 text-amber-500" />
          </div>

          <div className="space-y-2.5 my-1">
            {topAdvisors.map((adv, idx) => (
              <div key={adv.name} className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-5 h-5 rounded-full bg-black/10 dark:bg-white/15 flex items-center justify-center text-[9px] font-bold shrink-0">
                      {adv.name.charAt(0)}
                    </div>
                    <span className="font-bold text-gray-900 dark:text-white truncate">
                      {adv.name}
                    </span>
                  </div>
                  <span className="font-extrabold text-gray-900 dark:text-white shrink-0">
                    {formatCompact(adv.revenue)}
                  </span>
                </div>
                <div className="w-full bg-black/5 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[var(--theme-primary)] transition-all"
                    style={{ width: `${adv.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-[10px] pt-1.5 border-t border-gray-100 dark:border-zinc-800">
            <span className="text-gray-400">Total Workshop Team</span>
            <span className="font-extrabold text-gray-900 dark:text-white">16 Technicians</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardAnalyticsView;
