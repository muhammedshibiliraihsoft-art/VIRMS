import React from 'react';
import { Building2, TrendingUp, TrendingDown, DollarSign, ArrowRight } from 'lucide-react';
import { Data, Garage } from '../../types';
import { companyReportValues, garageReportValues } from '../../utils/selectors';

interface CompanyResultViewProps {
  data: Data;
  garages: Garage[];
  selectedGarage: string;
  onSelectGarage: (garageId: string) => void;
  onSelectRoute?: (routeKey: string) => void;
}

export const CompanyResultView: React.FC<CompanyResultViewProps> = ({
  data,
  garages,
  selectedGarage,
  onSelectGarage,
  onSelectRoute,
}) => {
  const formatINR = (val: number) => '₹' + Math.round(val).toLocaleString('en-IN');
  const comp = companyReportValues(data, selectedGarage);
  const totalInflow = comp.customerReceipts + comp.otherIncome;
  const netOperatingCash = totalInflow - comp.companyExpenses;
  const garageBreakdown = garageReportValues(data, selectedGarage);

  return (
    <div className="space-y-4 sm:space-y-5 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-[#f2ebe5] dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">
            EXECUTIVE ACCOUNTING
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            Company Result & Operating Performance
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium">
            Provisional accounting components and verified cash movements across workshops.
          </p>
        </div>

        {/* Garage Filter */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-zinc-800 border border-[#e2d8ce] dark:border-zinc-700 text-xs font-semibold text-gray-700 dark:text-gray-300">
          <Building2 className="w-3.5 h-3.5 text-gray-500" />
          <select
            value={selectedGarage}
            onChange={(e) => onSelectGarage(e.target.value)}
            className="bg-transparent border-none focus:outline-none cursor-pointer pr-2 font-bold"
          >
            <option value="all">All Garages</option>
            {garages.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="dashboard-card-orange text-white rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px] shadow-xs">
          <span className="text-[11px] font-medium text-white/90 leading-none">
            Net Operating Cash Flow
          </span>
          <span className="text-2xl sm:text-[27px] font-bold tracking-tight my-auto text-white">
            {formatINR(netOperatingCash)}
          </span>
        </div>

        <div className="dashboard-card-solid rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400 leading-none">
            Total Operational Inflow
          </span>
          <span className="text-2xl sm:text-[27px] font-bold tracking-tight my-auto text-gray-950 dark:text-white">
            {formatINR(totalInflow)}
          </span>
        </div>

        <div className="dashboard-card-solid rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400 leading-none">
            Company Operating Expenses
          </span>
          <span className="text-2xl sm:text-[27px] font-bold tracking-tight my-auto text-gray-950 dark:text-white">
            {formatINR(comp.companyExpenses)}
          </span>
        </div>

        <div className="dashboard-card-solid rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400 leading-none">
            Inventory Margin Realized
          </span>
          <span className="text-2xl sm:text-[27px] font-bold tracking-tight my-auto text-emerald-600 dark:text-emerald-400">
            +{formatINR(comp.inventoryMargin)}
          </span>
        </div>
      </div>

      {/* Breakdown Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Component Ledger */}
        <div className="dashboard-card-solid rounded-[24px] p-5 space-y-4">
          <h3 className="text-sm font-bold text-gray-950 dark:text-white">
            Component Inflows & Outflows
          </h3>
          <div className="space-y-2.5">
            <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50/60 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800">
              <div>
                <span className="text-xs font-bold text-gray-900 dark:text-white block">
                  Customer Job Receipts
                </span>
                <span className="text-[11px] text-gray-500">Collected from work order service billings</span>
              </div>
              <span className="text-xs font-bold font-mono text-emerald-600 dark:text-emerald-400">
                +{formatINR(comp.customerReceipts)}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50/60 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800">
              <div>
                <span className="text-xs font-bold text-gray-900 dark:text-white block">
                  Other Operational Income
                </span>
                <span className="text-[11px] text-gray-500">Workshop scrap metal, battery recycling</span>
              </div>
              <span className="text-xs font-bold font-mono text-emerald-600 dark:text-emerald-400">
                +{formatINR(comp.otherIncome)}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50/60 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800">
              <div>
                <span className="text-xs font-bold text-gray-900 dark:text-white block">
                  Operating Overhead Expenses
                </span>
                <span className="text-[11px] text-gray-500">Utilities, shop equipment, premises</span>
              </div>
              <span className="text-xs font-bold font-mono text-red-600 dark:text-red-400">
                -{formatINR(comp.companyExpenses)}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50/60 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800">
              <div>
                <span className="text-xs font-bold text-gray-900 dark:text-white block">
                  Running Capital (Unrecovered)
                </span>
                <span className="text-[11px] text-gray-500">Company contribution to stock vehicles</span>
              </div>
              <span className="text-xs font-bold font-mono text-gray-900 dark:text-white">
                {formatINR(comp.runningCapitalOpen)}
              </span>
            </div>
          </div>
        </div>

        {/* Branch Attributed Table */}
        <div className="dashboard-card-solid rounded-[24px] p-5 space-y-4">
          <h3 className="text-sm font-bold text-gray-950 dark:text-white">
            Attributed Branch Comparison
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#f0e7df] dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/30">
                  <th className="py-2.5 px-3 text-[11px] font-bold text-gray-600 dark:text-gray-300">Branch</th>
                  <th className="py-2.5 px-3 text-[11px] font-bold text-gray-600 dark:text-gray-300 text-right">Receipts</th>
                  <th className="py-2.5 px-3 text-[11px] font-bold text-gray-600 dark:text-gray-300 text-right">Expenses</th>
                  <th className="py-2.5 px-3 text-[11px] font-bold text-gray-600 dark:text-gray-300 text-right">Parts Margin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f5ede5] dark:divide-zinc-800/60">
                {garageBreakdown.map((g) => (
                  <tr key={g.garageId} className="hover:bg-gray-50/70 dark:hover:bg-zinc-800/40">
                    <td className="py-2.5 px-3 font-bold text-gray-900 dark:text-gray-100">{g.name}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-emerald-600 dark:text-emerald-400">
                      {formatINR(g.customerReceipts)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-red-600 dark:text-red-400">
                      {formatINR(g.companyExpenses)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-blue-600 dark:text-blue-400">
                      +{formatINR(g.inventoryMargin)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
