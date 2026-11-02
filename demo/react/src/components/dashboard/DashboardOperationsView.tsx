import React, { useState } from 'react';
import {
  Search,
  Plus,
  Wrench,
  Car,
  Clock,
  Calendar,
  ChevronDown,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Upload,
  X,
  Package,
  Activity,
  Layers,
  MapPin,
  Flame,
} from 'lucide-react';
import { Data } from '../../types';
import { useCanPresentBusinessWriteActions } from '../../auth/RolePresentationContext';
import { getFormDataSourceStatus } from '../../data/navigationRegistry';
import { DemoBadge } from '../shared/DemoBadge';

interface DashboardOperationsViewProps {
  data: Data;
  selectedGarage: string;
  onOpenFormModal: (type: any, context?: any) => void;
  onSelectRoute: (routeKey: string) => void;
}

export const DashboardOperationsView: React.FC<DashboardOperationsViewProps> = ({
  data,
  selectedGarage,
  onOpenFormModal,
  onSelectRoute,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeBay, setActiveBay] = useState<'Bay 1' | 'Bay 2'>('Bay 1');
  const [selectedDay, setSelectedDay] = useState('22');

  const { vehicles, jobs, garages } = data;

  const filteredVehicles =
    selectedGarage === 'all'
      ? vehicles
      : vehicles.filter((v) => v.garageId === selectedGarage);

  const filteredJobs =
    selectedGarage === 'all'
      ? jobs
      : jobs.filter((j) => j.garageId === selectedGarage);

  const stockVehiclesCount = filteredVehicles.filter(
    (v) => v.type === 'Stock / Investor' && v.status !== 'Sold'
  ).length;
  const openJobsCount = filteredJobs.filter((j) => j.status === 'Open').length;
  const completedJobsCount = filteredJobs.filter((j) => j.status === 'Completed').length;

  // 8 Calendar Days (Matching Target Design Image 2)
  const scheduleDays = [
    { day: 'Tue', date: '20', hasDot: false },
    { day: 'Wed', date: '21', hasDot: true },
    { day: 'Thu', date: '22', hasDot: true },
    { day: 'Fri', date: '23', hasDot: true, hasBigCircle: true },
    { day: 'Sat', date: '24', hasDot: false },
    { day: 'Sun', date: '25', hasDot: false },
    { day: 'Mon', date: '26', hasDot: true },
    { day: 'Tue', date: '27', hasDot: true },
  ];

  return (
    <div className="space-y-3.5 sm:space-y-4 animate-in fade-in duration-150">
      {/* =========================================================================
          ZONE 1: TOP SEARCH BAR & COMPACT KPI STATS (Matching Target Image 2)
          Left: Minimalist rounded Search input with circular search button
          Right: 3 Airy KPI counters (not heavy boxes) with value and percentage pill
         ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-4 items-center">
        {/* Search Bar (col-span-5) */}
        <div className="lg:col-span-5 bg-white dark:bg-zinc-900 border border-gray-200/80 dark:border-zinc-800 rounded-full px-4 py-2 flex items-center justify-between shadow-2xs">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search something..."
            className="w-full bg-transparent text-sm font-medium text-gray-900 dark:text-white placeholder-gray-400 outline-none pr-3"
          />
          <button
            onClick={() => onSelectRoute('All Vehicles')}
            className="w-8 h-8 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 flex items-center justify-center shrink-0 text-gray-600 dark:text-gray-300 transition cursor-pointer"
            title="Search vehicles & jobs"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* 3 Compact KPI Counters (col-span-7) */}
        <div className="lg:col-span-7 flex items-center justify-around sm:justify-end gap-6 sm:gap-10 px-1 select-none">
          {/* KPI 1: Total Stock Vehicles */}
          <div>
            <div className="text-[11px] font-semibold text-gray-400 leading-tight">
              Total Stock
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                {stockVehiclesCount}
              </span>
              <span className="px-1.5 py-0.5 rounded-full text-[9px] font-extrabold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                +18%
              </span>
            </div>
          </div>

          {/* KPI 2: Active Workshop Jobs */}
          <div>
            <div className="text-[11px] font-semibold text-gray-400 leading-tight">
              Active Jobs
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                {openJobsCount}
              </span>
              <span className="px-1.5 py-0.5 rounded-full text-[9px] font-extrabold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                -5%
              </span>
            </div>
          </div>

          {/* KPI 3: Completed Services */}
          <div>
            <div className="text-[11px] font-semibold text-gray-400 leading-tight">
              Completed Jobs
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                {completedJobsCount}
              </span>
              <span className="px-1.5 py-0.5 rounded-full text-[9px] font-extrabold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                +12%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          ZONE 2: ASYMMETRIC MIDDLE ROW (4 Cards matching Target Image 2)
          Card 1: Large Wide Workshop Flow Card with Speedometer Tracker (col-span-5)
          Card 2: Tall Narrow Solid Orange Accent Card (col-span-2)
          Card 3: Workshop Notes Nested Card (col-span-2)
          Card 4: Most Clients by Country / Garage Network Map Card (col-span-3)
         ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3 sm:gap-4 items-stretch">
        {/* Card 1: Workshop Flow & Capacity with prominent Speedometer Tracker (lg:col-span-5) */}
        <div className="lg:col-span-5 dashboard-card-solid rounded-[24px] p-5 sm:p-6 flex flex-col justify-between">
          {/* Header */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-gray-950 dark:text-white tracking-tight">
              Workshop Flow & Capacity
            </span>
            <button
              onClick={() => onSelectRoute('Garage Jobs')}
              className="w-6 h-6 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 flex items-center justify-center text-gray-500 hover:text-black dark:hover:text-white transition cursor-pointer"
              title="Add job order"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Middle: Turnaround Metric + Large High-Fidelity Speedometer Arc Tracker */}
          <div className="my-3 flex items-center justify-between gap-4">
            {/* Left Metric */}
            <div className="space-y-1">
              <div className="text-[11px] font-semibold text-gray-400 leading-none">
                Avg Response Time:
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl sm:text-4xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                  368
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                  ⚡ Fast
                </span>
              </div>
              <div className="text-xs font-semibold text-gray-400">
                Second
              </div>
            </div>

            {/* Right: Semi-Circular Speedometer Arc Tracker (Matching Target Image 2) */}
            <div className="relative w-40 h-24 flex items-end justify-center select-none shrink-0">
              <svg viewBox="0 0 130 75" className="w-40 h-24 overflow-visible">
                <defs>
                  <linearGradient id="trackerGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="var(--theme-primary)" />
                    <stop offset="100%" stopColor="var(--theme-primary-hover, var(--theme-primary))" />
                  </linearGradient>
                </defs>

                {/* Gray Background Track */}
                <path
                  d="M 12 70 A 53 53 0 0 1 118 70"
                  fill="none"
                  stroke="#e5e7eb"
                  strokeWidth="14"
                  strokeLinecap="round"
                  className="dark:stroke-zinc-800"
                />

                {/* Theme Primary Active Filled Arc (~68% filled) */}
                <path
                  d="M 12 70 A 53 53 0 0 1 97 27"
                  fill="none"
                  stroke="url(#trackerGrad)"
                  strokeWidth="14"
                  strokeLinecap="round"
                />

                {/* Center Directional Arrow Needle pointing into arc (Matching Image 2) */}
                <g transform="translate(65, 70)">
                  <polygon
                    points="0,-4 18,-24 4,-26"
                    fill="#18181b"
                    className="dark:fill-white"
                  />
                  <polygon
                    points="0,-4 4,-26 -4,-18"
                    fill="#3f3f46"
                    className="dark:fill-zinc-300"
                  />
                </g>
              </svg>
            </div>
          </div>

          {/* Bottom Tool Pills Row (Matching Image 2: Circular badges + Featured status pill) */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-zinc-800/80 gap-2 flex-wrap">
            {/* 3 Circular Avatar/Tool Icons with Notification Counts */}
            <div className="flex items-center gap-2">
              <div className="relative w-9 h-9 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center text-gray-700 dark:text-gray-200 shadow-2xs">
                <Wrench className="w-4 h-4" />
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[var(--theme-primary)] text-white text-[9px] font-bold flex items-center justify-center">
                  10
                </span>
              </div>
              <div className="relative w-9 h-9 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center text-gray-700 dark:text-gray-200 shadow-2xs">
                <Car className="w-4 h-4" />
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[var(--theme-primary)] text-white text-[9px] font-bold flex items-center justify-center">
                  8
                </span>
              </div>
              <div className="relative w-9 h-9 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center text-gray-700 dark:text-gray-200 shadow-2xs">
                <Package className="w-4 h-4" />
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[var(--theme-primary)] text-white text-[9px] font-bold flex items-center justify-center">
                  4
                </span>
              </div>
            </div>

            {/* Featured Station Pill (Matching "Slack Application / New message") */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/5 dark:bg-white/10 text-xs font-semibold text-gray-800 dark:text-gray-200">
              <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
              <div className="text-[11px] leading-tight">
                <span className="font-bold">Bay 1 Active</span>
                <span className="text-gray-400 text-[10px] ml-1">Repairing</span>
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: Tall Narrow Solid Orange Accent Card (lg:col-span-2) */}
        <div className="lg:col-span-2 dashboard-card-orange rounded-[24px] p-5 text-white flex flex-col justify-between shadow-xs select-none min-h-[220px]">
          {/* Top Title & Subtle Action Button */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold tracking-tight text-white/95">
              Manage Quotes
            </span>
            <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-white/80 text-[10px]">
              ✕
            </div>
          </div>

          {/* Center: White Pill Button */}
          {canPresentWriteActions && (
            <div className="my-auto py-2">
              <button
                onClick={() => onOpenFormModal('job')}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-full bg-white text-gray-950 font-extrabold text-xs shadow-xs hover:bg-white/95 transition cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                {getFormDataSourceStatus('job') === 'demo' && <DemoBadge size="compact" />}
                <span>Create New</span>
              </button>
            </div>
          )}

          {/* Bottom: Massive Bold Number with Subtitle */}
          <div>
            <div className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-none">
              127
            </div>
            <div className="text-[10px] text-white/80 mt-1 font-medium leading-tight">
              Average in <br /> a month
            </div>
          </div>
        </div>

        {/* Card 3: Meeting / Workshop Notes Nested Card (lg:col-span-2) */}
        <div className="lg:col-span-2 dashboard-card-solid rounded-[24px] p-5 flex flex-col justify-between min-h-[220px]">
          {/* Header */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-950 dark:text-white tracking-tight">
              Meeting Notes
            </span>
            <button
              onClick={() => onSelectRoute('Garage Jobs')}
              className="w-6 h-6 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 flex items-center justify-center text-gray-500 hover:text-black dark:hover:text-white transition cursor-pointer"
            >
              <Plus className="w-3 h-3" />
            </button>
          </div>

          {/* Nested Card Container (Matching Image 2's inner note box) */}
          <div className="bg-white dark:bg-zinc-800/90 border border-gray-200/80 dark:border-zinc-700/80 rounded-2xl p-3 my-2 shadow-2xs space-y-1.5">
            <div className="flex items-center justify-between text-[10px] text-gray-400 font-semibold">
              <span>2h ago</span>
              <span className="text-gray-300 dark:text-zinc-500 font-mono">•••</span>
            </div>
            <div className="text-xs font-extrabold text-gray-900 dark:text-white leading-snug line-clamp-2">
              Brainstorming for Product Development
            </div>
            <div className="flex items-center gap-1.5 pt-1">
              <span className="w-2 h-2 rounded-full bg-[var(--theme-primary)]" />
              <span className="text-[10px] font-bold text-gray-600 dark:text-gray-300 truncate">
                Meeta Project
              </span>
            </div>
          </div>

          <button
            onClick={() => onSelectRoute('Garage Jobs')}
            className="text-[10px] font-bold text-[var(--theme-primary)] hover:underline text-left cursor-pointer"
          >
            Open note details →
          </button>
        </div>

        {/* Card 4: Most Clients by Country / Garage Network Map Card (lg:col-span-3) */}
        <div className="lg:col-span-3 dashboard-card-solid rounded-[24px] p-5 flex flex-col justify-between relative overflow-hidden min-h-[220px]">
          {/* Header */}
          <div className="flex items-center justify-between relative z-10">
            <span className="text-xs font-bold text-gray-950 dark:text-white tracking-tight">
              Most Clients by Country
            </span>
            <button
              onClick={() => onSelectRoute('Settings')}
              className="w-6 h-6 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 flex items-center justify-center text-gray-500 hover:text-black dark:hover:text-white transition cursor-pointer"
            >
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Stylized Vector Map Illustration Background with Country Pin */}
          <div className="relative my-auto py-2 flex items-center justify-center z-0">
            {/* Faint Road/Map Grid Lines */}
            <svg viewBox="0 0 160 80" className="w-full h-20 opacity-30 dark:opacity-20">
              <path
                d="M 10 40 Q 60 10 110 50 T 150 20"
                fill="none"
                stroke="#9ca3af"
                strokeWidth="1.5"
              />
              <path
                d="M 30 10 Q 50 60 90 40 T 140 70"
                fill="none"
                stroke="#9ca3af"
                strokeWidth="1.2"
              />
              <path
                d="M 10 70 L 150 15"
                fill="none"
                stroke="#d1d5db"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
            </svg>

            {/* Circular Flag / Location Pin (Matching Image 2's US Flag circle) */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-9 h-9 rounded-full ring-4 ring-white dark:ring-zinc-800 shadow-md overflow-hidden bg-blue-900 flex items-center justify-center border border-gray-200">
                {/* Stylized Flag Graphic */}
                <div className="w-full h-full flex flex-col justify-between py-1 bg-red-600">
                  <div className="h-1 bg-white" />
                  <div className="h-1 bg-white" />
                  <div className="h-1 bg-white" />
                  <div className="absolute top-0 left-0 w-4 h-4 bg-blue-800 rounded-br-md" />
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Floating Dark Pill (Matching Image 2's 48 United States) */}
          <div className="relative z-10 flex items-center justify-between p-1.5 pl-2.5 rounded-full bg-white/90 dark:bg-zinc-800/90 border border-gray-200/80 dark:border-zinc-700 shadow-2xs">
            {/* Left Graphic Icon */}
            <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center text-white text-[9px] font-bold shrink-0">
              🌆
            </div>

            {/* Center Count & Label */}
            <div className="flex items-baseline gap-1.5 px-2">
              <span className="text-base font-extrabold text-gray-950 dark:text-white">
                48
              </span>
              <span className="text-[10px] text-gray-500 dark:text-gray-400 font-semibold">
                United States
              </span>
            </div>

            {/* Right Action Button */}
            <button
              onClick={() => onSelectRoute('Settings')}
              className="w-6 h-6 rounded-full bg-[#18181b] dark:bg-white text-white dark:text-black flex items-center justify-center transition shrink-0 cursor-pointer"
            >
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* =========================================================================
          ZONE 3: LOWER SECTION (Chart Left & Wide Schedule Right)
          Card 1 (Left): Project Deals Bar Chart with Hatched Past Bars & Active Month (lg:col-span-5)
          Card 2 (Right): Meeting / Workshop Schedule with Today's Floating Card (lg:col-span-7)
         ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-4 items-stretch">
        {/* Left: Project Deals / Job Orders Bar Chart (lg:col-span-5) */}
        <div className="lg:col-span-5 dashboard-card-solid rounded-[24px] p-5 sm:p-6 flex flex-col justify-between">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 cursor-pointer">
              <span className="text-sm font-bold text-gray-950 dark:text-white tracking-tight">
                Project Deals
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
            </div>

            <div className="flex items-center gap-1.5">
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/5 dark:bg-white/10 text-[10px] font-bold text-gray-600 dark:text-gray-300">
                <span>Last 7 months</span>
                <ChevronDown className="w-3 h-3 text-gray-400" />
              </div>
              <button
                className="w-6 h-6 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center text-gray-500 hover:text-black dark:hover:text-white transition cursor-pointer"
                title="Export report"
              >
                <Upload className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* SVG Bar Chart with Diagonal Hatch Pattern & Active Highlighted Solid Bar */}
          <div className="w-full pt-2">
            <svg viewBox="0 0 320 160" className="w-full h-44 overflow-visible">
              <defs>
                {/* Diagonal Stripes Hatch Pattern for Past Months (Matching Image 2) */}
                <pattern
                  id="targetDealsHatch"
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
                    stroke="#9ca3af"
                    strokeWidth="1.6"
                    opacity="0.45"
                  />
                </pattern>
              </defs>

              {/* Dotted Horizontal Gridlines and Y-axis Numbers */}
              {[250, 200, 150, 100].map((v, i) => (
                <g key={v}>
                  <text
                    x="20"
                    y={i * 28 + 14}
                    textAnchor="end"
                    className="fill-gray-400 text-[8px] font-medium"
                  >
                    {v}
                  </text>
                  <line
                    x1="26"
                    y1={i * 28 + 11}
                    x2="315"
                    y2={i * 28 + 11}
                    stroke="#e5e7eb"
                    strokeDasharray="2 2"
                    className="dark:stroke-zinc-800"
                  />
                </g>
              ))}

              {/* 5 Monthly Bars (4 Hatched Past Bars + 1 Solid Theme Accent Bar with Active Dot & Tooltip) */}
              {[
                { label: 'May', h: 62 },
                { label: 'Jun', h: 78 },
                { label: 'Jul', h: 90 },
                { label: 'Aug', h: 104 },
                { label: 'Oct', h: 122, isCurrent: true, value: 230 },
                { label: 'Nov', h: 74 },
                { label: 'Dec', h: 86 },
              ].map((bar, idx) => {
                const x = 36 + idx * 40;
                const barWidth = 24;
                const y = 130 - bar.h;

                return (
                  <g key={bar.label} className="group cursor-pointer">
                    {bar.isCurrent ? (
                      /* Active Month Bar: Solid Theme Accent with White Dot and Floating Black Pill */
                      <>
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={bar.h}
                          rx="12"
                          fill="var(--theme-primary)"
                        />
                        {/* Circular Dot near top of active bar */}
                        <circle
                          cx={x + barWidth / 2}
                          cy={y + 10}
                          r="3"
                          fill="#ffffff"
                        />
                        {/* Floating Black Capsule with Value 230 */}
                        <rect
                          x={x - 2}
                          y={y - 20}
                          width={28}
                          height="15"
                          rx="7.5"
                          fill="#18181b"
                        />
                        <text
                          x={x + barWidth / 2}
                          y={y - 9}
                          textAnchor="middle"
                          fill="#ffffff"
                          fontSize="8.5"
                          fontWeight="extrabold"
                        >
                          {bar.value}
                        </text>
                      </>
                    ) : (
                      /* Past/Future Bars: Diagonal Hatch Pattern with Rounded Outline */
                      <>
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={bar.h}
                          rx="4"
                          fill="url(#targetDealsHatch)"
                        />
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={bar.h}
                          rx="4"
                          fill="none"
                          stroke="#d1d5db"
                          strokeWidth="1"
                          className="dark:stroke-zinc-700"
                        />
                      </>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Right: Meeting Schedule / Workshop Bay Schedule (lg:col-span-7) */}
        <div className="lg:col-span-7 dashboard-card-solid rounded-[24px] p-5 sm:p-6 flex flex-col justify-between relative overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold text-gray-950 dark:text-white tracking-tight">
              Meeting Schedule
            </span>
            <div className="flex items-center gap-1.5">
              <div className="px-3 py-1 rounded-full bg-black/5 dark:bg-white/10 text-[10px] font-bold text-gray-600 dark:text-gray-300">
                October 2026
              </div>
              <button
                onClick={() => onSelectRoute('Garage Jobs')}
                className="w-6 h-6 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 flex items-center justify-center text-gray-500 hover:text-black dark:hover:text-white transition cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Calendar Row: Left/Right Chevrons + 8 Day Columns */}
          <div className="flex items-center justify-between gap-1 my-2 py-1">
            <button className="p-1 rounded-full text-gray-400 hover:text-black dark:hover:text-white transition">
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div className="flex-1 grid grid-cols-8 gap-1 text-center">
              {scheduleDays.map((sd) => {
                const isSelected = selectedDay === sd.date;
                return (
                  <div
                    key={sd.date}
                    onClick={() => setSelectedDay(sd.date)}
                    className={`flex flex-col items-center py-2 px-1 rounded-2xl transition cursor-pointer ${
                      isSelected
                        ? 'bg-[#18181b] text-white shadow-xs'
                        : 'hover:bg-black/5 dark:hover:bg-white/5 text-gray-800 dark:text-gray-200'
                    }`}
                  >
                    <span className={`text-[9px] font-semibold ${isSelected ? 'text-gray-300' : 'text-gray-400'}`}>
                      {sd.day}
                    </span>
                    <span className="text-sm font-extrabold mt-0.5">
                      {sd.date}
                    </span>

                    {/* Indicator Dot */}
                    <div className="mt-2 h-4 flex items-center justify-center">
                      {sd.hasBigCircle ? (
                        <span className="w-3 h-3 rounded-full bg-[var(--theme-primary)]" />
                      ) : sd.hasDot ? (
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            isSelected ? 'bg-white' : 'bg-gray-300 dark:bg-zinc-600'
                          }`}
                        />
                      ) : (
                        <span className="w-1.5 h-1.5 rounded-full bg-transparent" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <button className="p-1 rounded-full text-gray-400 hover:text-black dark:hover:text-white transition">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Bottom Area: Segmented Pill Toggle on Left + Floating Dark Card on Right */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 pt-3 border-t border-gray-100 dark:border-zinc-800/80">
            {/* Segmented Pill Toggle: [ Fluento | Ember ] / in our case [ Fluento | Ember ] */}
            <div className="flex items-center p-1 rounded-full bg-[#18181b] text-white text-xs font-bold w-fit shadow-xs">
              <button
                onClick={() => setActiveBay('Bay 1')}
                className={`px-3 py-1.5 rounded-full transition cursor-pointer flex items-center gap-1.5 ${
                  activeBay === 'Bay 1'
                    ? 'bg-zinc-800 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-indigo-400" />
                <span>Fluento</span>
              </button>
              <button
                onClick={() => setActiveBay('Bay 2')}
                className={`px-3 py-1.5 rounded-full transition cursor-pointer flex items-center gap-1.5 ${
                  activeBay === 'Bay 2'
                    ? 'bg-white text-black font-extrabold'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[var(--theme-primary)]" />
                <span>Ember</span>
              </button>
            </div>

            {/* Floating Dark Popover Card (Matching Image 2's "Upcoming Today's Meeting") */}
            <div className="bg-[#18181b] text-white rounded-2xl p-4 shadow-xl flex-1 max-w-sm sm:ml-auto space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white tracking-tight">
                  Upcoming Today&apos;s Meeting
                </span>
                <button className="text-gray-400 hover:text-white transition">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Tag Pills */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[var(--theme-primary)] text-white">
                  Media Project
                </span>
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-800 text-gray-300">
                  <Clock className="w-2.5 h-2.5 text-gray-400" />
                  <span>10 - 11 AM</span>
                </span>
              </div>

              {/* Bottom Team Avatars + Action Button */}
              <div className="flex items-center justify-between pt-1">
                <div className="flex items-center -space-x-1.5">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-stone-700 to-stone-500 ring-2 ring-[#18181b] text-white text-[9px] font-bold flex items-center justify-center">
                    JD
                  </div>
                  <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-amber-600 to-amber-400 ring-2 ring-[#18181b] text-white text-[9px] font-bold flex items-center justify-center">
                    AK
                  </div>
                  <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-emerald-600 to-emerald-400 ring-2 ring-[#18181b] text-white text-[9px] font-bold flex items-center justify-center">
                    LM
                  </div>
                </div>

                <button
                  onClick={() => onSelectRoute('Garage Jobs')}
                  className="w-7 h-7 rounded-full bg-white/20 hover:bg-white/30 text-white flex items-center justify-center transition cursor-pointer"
                  title="Join meeting / job details"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardOperationsView;
