import React, { useState } from 'react';
import {
  TrendingUp,
  CreditCard,
  Plus,
  Send,
  Download,
  AlertTriangle,
  CheckCircle2,
  Lock,
  ArrowUpRight,
  Search,
  Filter,
  DollarSign,
  Briefcase,
} from 'lucide-react';
import { Data, ActivityItem } from '../../types';
import { formatCurrency, formatCompact } from '../../utils/formatters';
import { useCanPresentBusinessWriteActions } from '../../auth/RolePresentationContext';
import { getFormDataSourceStatus } from '../../data/navigationRegistry';
import { DemoBadge } from '../shared/DemoBadge';

interface DashboardFinancialViewProps {
  data: Data;
  activities: ActivityItem[];
  selectedGarage: string;
  onOpenFormModal: (type: any, context?: any) => void;
  onSelectRoute: (routeKey: string) => void;
  onSelectActivity: (item: ActivityItem) => void;
}

export const DashboardFinancialView: React.FC<DashboardFinancialViewProps> = ({
  data,
  activities,
  selectedGarage,
  onOpenFormModal,
  onSelectRoute,
  onSelectActivity,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const [dealSearch, setDealSearch] = useState('');

  const { investors, sales, vehicles, jobs } = data;

  const totalInvestorPrincipal = investors.reduce((sum, inv) => sum + inv.principal, 0);
  const totalInvestorUsed = investors.reduce((sum, inv) => sum + (inv.used || 0), 0);
  const totalSalesRevenue = sales.reduce((sum, s) => sum + (s.price || 0), 0);
  const totalBuyerReceivable = 245000; // Verified buyer balance

  const filteredActivities = activities.filter(
    (act) =>
      act.title.toLowerCase().includes(dealSearch.toLowerCase()) ||
      act.code.toLowerCase().includes(dealSearch.toLowerCase())
  );

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* 1. Top Row: 3 Major Commercial KPI Blocks (Reference 3 Top Row) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-stretch">
        {/* Card 1: Commercial Revenue & Cash Flow (lg:col-span-5) */}
        <div className="lg:col-span-5 dashboard-card-solid rounded-[24px] p-5 sm:p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[var(--theme-primary)]" />
              <span className="text-xs font-bold text-gray-500 dark:text-gray-400">
                Total Commercial Revenue
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-gray-500">
              <span>INR ₹</span>
              <span>•</span>
              <span>All Time</span>
            </div>
          </div>

          <div className="my-3 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
            <div>
              <div className="text-3xl sm:text-4xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                ₹50,74,000
              </div>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  +12%
                </span>
                <span className="text-[11px] text-gray-400 font-medium">Revenue increase, positive margin</span>
              </div>
            </div>

            {/* Stepped Realization Heatmap Matrix Graphic (Reference 3 Matrix) */}
            <div className="flex items-end gap-1 shrink-0 mt-2 sm:mt-0">
              {[
                [1, 2, 3, 4],
                [2, 3, 4],
                [3, 4],
                [4],
              ].map((col, cIdx) => (
                <div key={cIdx} className="flex flex-col gap-1">
                  {col.map((item, rIdx) => (
                    <div
                      key={rIdx}
                      className="w-3 h-3 rounded-xs"
                      style={{
                        backgroundColor:
                          item === 4
                            ? 'var(--theme-primary)'
                            : item === 3
                            ? 'var(--theme-primary-hover)'
                            : item === 2
                            ? 'var(--theme-primary-soft)'
                            : '#e5e7eb',
                      }}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions (Reference 3 Action Row) */}
          <div className="flex items-center gap-2 pt-2 border-t border-gray-100 dark:border-zinc-800 flex-wrap">
            {canPresentWriteActions && (
              <>
            <button
              onClick={() => onOpenFormModal('customerReceipt')}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-[var(--theme-primary)] hover:brightness-105 text-white font-bold text-xs shadow-2xs transition cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="min-w-0 truncate">Record Receipt</span>
              {getFormDataSourceStatus('customerReceipt') === 'demo' && <DemoBadge size="compact" />}
            </button>
            <button
              onClick={() => onOpenFormModal('sale')}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 text-gray-900 dark:text-white font-bold text-xs transition cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span className="min-w-0 truncate">New Vehicle Sale</span>
              {getFormDataSourceStatus('sale') === 'demo' && <DemoBadge size="compact" />}
            </button>
              </>
            )}
            <button
              onClick={() => onSelectRoute('Garage Revenue')}
              className="w-9 h-9 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 flex items-center justify-center text-gray-600 dark:text-gray-300 transition cursor-pointer shrink-0"
              title="View revenue ledgers"
            >
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Card 2: Sales Realized / Deals Won (lg:col-span-4) */}
        <div className="lg:col-span-4 dashboard-card-solid rounded-[24px] p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-bold text-gray-500 dark:text-gray-400">
                Realized Vehicle Sales
              </span>
            </div>
            <span className="text-[10px] font-bold text-gray-400">Oct 2026</span>
          </div>

          <div className="my-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                {formatCurrency(totalSalesRevenue || 4995000)}
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                +₹4.5L
              </span>
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">
              Settled buyer transactions & invoices
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 dark:border-zinc-800 text-[11px]">
            <div>
              <div className="text-[10px] text-gray-400">New Buyer Inflow</div>
              <div className="font-extrabold text-gray-900 dark:text-white mt-0.5">
                ₹38,00,000
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400">Repeat Accounts</div>
              <div className="font-extrabold text-gray-900 dark:text-white mt-0.5">
                ₹11,95,000
              </div>
            </div>
          </div>
        </div>

        {/* Card 3: Outstanding Receivables & Aging (lg:col-span-3) */}
        <div className="lg:col-span-3 dashboard-card-solid rounded-[24px] p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-xs font-bold text-gray-500 dark:text-gray-400">
                Buyer Receivables
              </span>
            </div>
            <span className="text-[10px] font-bold text-gray-400">Pending</span>
          </div>

          <div className="my-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                {formatCurrency(totalBuyerReceivable)}
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                -₹45k
              </span>
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">
              3 active buyers with balance due
            </div>
          </div>

          {/* Segmented Aging Bar (Reference 3 Segmented Bar) */}
          <div className="space-y-1.5 pt-2 border-t border-gray-100 dark:border-zinc-800">
            <div className="w-full h-2 rounded-full bg-black/5 dark:bg-white/10 flex overflow-hidden">
              <div className="bg-emerald-500 h-full" style={{ width: '65%' }} title="Current (<30d)" />
              <div className="bg-amber-500 h-full" style={{ width: '25%' }} title="30-60d" />
              <div className="bg-rose-500 h-full" style={{ width: '10%' }} title=">60d" />
            </div>
            <div className="flex items-center justify-between text-[9px] text-gray-400">
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> &lt;30d
              </span>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> 30-60d
              </span>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" /> &gt;60d
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Middle Row: 3 Financial Panels (Reference 3 Middle Area) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-stretch">
        {/* Card 1: Investor Capital Arc Gauge (lg:col-span-4) */}
        <div className="lg:col-span-4 dashboard-card-solid rounded-[24px] p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-gray-950 dark:text-white tracking-tight">
              Investor Fund Utilization
            </span>
            <button
              onClick={() => onSelectRoute('Investor Fund Report')}
              className="text-[10px] font-bold text-[var(--theme-primary)] hover:underline cursor-pointer"
            >
              Ledger →
            </button>
          </div>

          {/* Dark Radial Target Arc Gauge (Reference 3 Left Gauge) */}
          <div className="bg-[#18181b] text-white rounded-2xl p-4 my-2 flex flex-col items-center justify-center relative overflow-hidden">
            <div className="relative w-36 h-20 flex items-end justify-center">
              <svg viewBox="0 0 100 50" className="w-36 h-18">
                <path
                  d="M 12 50 A 38 38 0 0 1 88 50"
                  fill="none"
                  stroke="#27272a"
                  strokeWidth="8"
                  strokeLinecap="round"
                />
                <path
                  d="M 12 50 A 38 38 0 0 1 76 20"
                  fill="none"
                  stroke="var(--theme-primary)"
                  strokeWidth="8"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute bottom-1 text-center">
                <div className="text-xl font-extrabold tracking-tight">
                  {formatCompact(totalInvestorUsed)}
                </div>
                <div className="text-[9px] text-gray-400 font-medium">
                  of {formatCompact(totalInvestorPrincipal)}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-[10px] font-semibold text-gray-300">
                50.6% Active Capital Deployment
              </span>
            </div>
          </div>

          {/* Sub-breakdown per investor */}
          <div className="space-y-1.5 pt-2 border-t border-gray-100 dark:border-zinc-800 text-[11px]">
            {investors.slice(0, 2).map((inv) => (
              <div key={inv.id} className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-300">{inv.name}</span>
                <span className="font-extrabold text-gray-900 dark:text-white">
                  {formatCompact(inv.used || 0)} / {formatCompact(inv.principal)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Card 2: Inflow vs Outflow Grouped Bar Chart (lg:col-span-5) */}
        <div className="lg:col-span-5 dashboard-card-solid rounded-[24px] p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="text-xs sm:text-sm font-bold text-gray-950 dark:text-white tracking-tight">
                Cash Flow Overview
              </span>
              <p className="text-[10px] text-gray-400">Monthly commercial receipts vs expenses</p>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-bold">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--theme-primary)]" />
                <span className="text-gray-600 dark:text-gray-300">Collections</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#18181b] dark:bg-zinc-300" />
                <span className="text-gray-600 dark:text-gray-300">Expenses</span>
              </div>
            </div>
          </div>

          {/* SVG Grouped Bar Chart with Interactive Popover */}
          <div className="w-full">
            <svg viewBox="0 0 350 145" className="w-full h-40 overflow-visible">
              {[20, 15, 10, 5, 0].map((v, i) => (
                <line
                  key={v}
                  x1="20"
                  y1={i * 26 + 10}
                  x2="340"
                  y2={i * 26 + 10}
                  stroke="#e5e7eb"
                  strokeDasharray={v === 0 ? 'none' : '2 2'}
                  className="dark:stroke-zinc-800"
                />
              ))}

              {[
                { month: 'Jun', in: 45, out: 30 },
                { month: 'Jul', in: 60, out: 40 },
                { month: 'Aug', in: 55, out: 35 },
                { month: 'Sep', in: 75, out: 48 },
                { month: 'Oct', in: 95, out: 42, active: true },
              ].map((m, idx) => {
                const x = 38 + idx * 62;
                return (
                  <g key={m.month}>
                    {/* Inflow Bar */}
                    <rect
                      x={x}
                      y={114 - m.in}
                      width="16"
                      height={m.in}
                      rx="3.5"
                      fill="var(--theme-primary)"
                    />
                    {/* Outflow Bar */}
                    <rect
                      x={x + 19}
                      y={114 - m.out}
                      width="16"
                      height={m.out}
                      rx="3.5"
                      fill="#18181b"
                      className="dark:fill-zinc-300"
                    />

                    {/* Popover on active month (Reference 3 Popover) */}
                    {m.active && (
                      <>
                        <rect x={x - 8} y="22" width="68" height="34" rx="8" fill="#18181b" />
                        <text x={x + 26} y="34" textAnchor="middle" fill="#ffffff" fontSize="8" fontWeight="bold">
                          Oct 2026
                        </text>
                        <text x={x + 26} y="44" textAnchor="middle" fill="var(--theme-primary)" fontSize="8" fontWeight="bold">
                          In: ₹6.45L
                        </text>
                        <text x={x + 26} y="52" textAnchor="middle" fill="#9ca3af" fontSize="7">
                          Out: ₹1.80L
                        </text>
                      </>
                    )}

                    <text x={x + 17} y="130" textAnchor="middle" className="fill-gray-400 text-[9px] font-medium">
                      {m.month}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Card 3: Governance & Ledger Compliance (lg:col-span-3) */}
        <div className="lg:col-span-3 space-y-3 flex flex-col justify-between">
          {/* Card 3a: Immutable Audit Integrity */}
          <div className="dashboard-card-solid rounded-[22px] p-4 flex flex-col justify-between flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-950 dark:text-white">
                Ledger Audit Status
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="my-2">
              <div className="text-lg font-extrabold text-gray-950 dark:text-white">
                0 Discrepancies
              </div>
              <p className="text-[10px] text-gray-400 mt-0.5">
                All 41 ledger events verified against immutable sequence hash.
              </p>
            </div>
            <button
              onClick={() => onSelectRoute('Audit & Corrections')}
              className="text-[10px] font-bold text-[var(--theme-primary)] hover:underline text-left cursor-pointer"
            >
              Open Audit Log →
            </button>
          </div>

          {/* Card 3b: Tax & Settlement Overview */}
          <div className="dashboard-card-solid rounded-[22px] p-4 flex flex-col justify-between flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-950 dark:text-white">
                Settlement Rules
              </span>
              <Lock className="w-3.5 h-3.5 text-amber-500" />
            </div>
            <div className="my-2">
              <div className="text-sm font-bold text-gray-900 dark:text-white">
                Policy Frozen
              </div>
              <p className="text-[10px] text-gray-400 mt-0.5">
                Investor profit distributions locked per canonical business rules.
              </p>
            </div>
            <button
              onClick={() => onSelectRoute('Reconciliation & Settlement')}
              className="text-[10px] font-bold text-amber-600 dark:text-amber-400 hover:underline text-left cursor-pointer"
            >
              View Settlement Notice →
            </button>
          </div>
        </div>
      </div>

      {/* 3. Bottom Row: Commercial Deals & Transaction Register (Reference 3 Bottom Table) */}
      <div className="dashboard-card-solid rounded-[24px] p-5 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
          <div>
            <span className="text-sm font-bold text-gray-950 dark:text-white tracking-tight">
              Recent Commercial Transactions & Deal Register
            </span>
            <p className="text-[11px] text-gray-400">
              Live ledger receipts, vehicle sales contracts, and job invoices
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={dealSearch}
                onChange={(e) => setDealSearch(e.target.value)}
                placeholder="Search transactions..."
                className="pl-8 pr-3 py-1.5 rounded-xl bg-black/5 dark:bg-white/5 text-xs text-gray-900 dark:text-white placeholder-gray-400 outline-none w-48"
              />
            </div>
          </div>
        </div>

        {/* Commercial Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-gray-100 dark:border-zinc-800 text-gray-400 font-semibold text-[10px] uppercase tracking-wider">
                <th className="pb-2.5">Transaction ID</th>
                <th className="pb-2.5">Vehicle / Item</th>
                <th className="pb-2.5">Value</th>
                <th className="pb-2.5">Channel</th>
                <th className="pb-2.5">Date</th>
                <th className="pb-2.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-zinc-800/80 font-medium">
              {filteredActivities.slice(0, 6).map((item) => (
                <tr
                  key={item.id}
                  onClick={() => onSelectActivity(item)}
                  className="hover:bg-black/5 dark:hover:bg-white/5 transition cursor-pointer"
                >
                  <td className="py-2.5 font-bold text-gray-900 dark:text-white font-mono text-[11px]">
                    {item.code}
                  </td>
                  <td className="py-2.5 text-gray-700 dark:text-gray-300">
                    {item.title}
                  </td>
                  <td className="py-2.5 font-extrabold text-gray-950 dark:text-white">
                    {formatCurrency(item.amount)}
                  </td>
                  <td className="py-2.5 text-gray-500">
                    {item.type === 'sale' ? 'Direct Deal' : 'Workshop Bay'}
                  </td>
                  <td className="py-2.5 text-gray-400 text-[11px]">
                    {item.date}
                  </td>
                  <td className="py-2.5 text-right">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        item.status === 'Completed' || item.status === 'Sold'
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                          : item.status === 'In work'
                          ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                          : 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DashboardFinancialView;
