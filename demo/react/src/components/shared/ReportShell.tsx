import React, { useState } from 'react';
import {
  BarChart3,
  Search,
  Filter,
  FileSpreadsheet,
  Download,
  Printer,
  ChevronRight,
  ArrowLeft,
  Building2,
  Calendar,
} from 'lucide-react';
import { Data, Garage } from '../../types';
import { getReportData, ReportDefinition } from '../../utils/selectors';

interface ReportShellProps {
  activeRoute: string;
  data: Data;
  garages: Garage[];
  selectedGarage: string;
  onSelectGarage: (garageId: string) => void;
  onSelectRoute: (routeKey: string) => void;
}

const ALL_REPORT_CARDS = [
  { id: 'Company Consolidated', title: 'Company Consolidated', category: 'Executive', desc: 'Combined operational results, revenues and expenses' },
  { id: 'Garage-wise', title: 'Garage-wise Performance', category: 'Branch', desc: 'Attributed components and receipts by workshop' },
  { id: 'Vehicle Cost', title: 'Vehicle Cost Ledger', category: 'Vehicles', desc: 'Purchase, expense and parts issue breakdown' },
  { id: 'Investor Fund Report', title: 'Investor Fund Ledger', category: 'Investment', desc: 'Capital deployment, reserves and available funds' },
  { id: 'Company Expenses', title: 'Expense Register', category: 'Accounting', desc: 'Vehicle and company operational expenses' },
  { id: 'Garage Jobs', title: 'Garage Jobs & Work Orders', category: 'Operations', desc: 'Work order billings, receipts and balances' },
  { id: 'Inventory Current Stock', title: 'Inventory Current Stock', category: 'Inventory', desc: 'Stock quantities, batch costs and valuations' },
  { id: 'Inventory Purchases', title: 'Inventory Purchases', category: 'Inventory', desc: 'Procurement history and received batches' },
  { id: 'Inventory Issues', title: 'Inventory Issues', category: 'Inventory', desc: 'Parts dispensed to vehicles and job cards' },
  { id: 'Product Margin', title: 'Product Margin Analysis', category: 'Inventory', desc: 'Realized parts markup and profit margin' },
  { id: 'Sales', title: 'Vehicle Sales Register', category: 'Sales', desc: 'Vehicle sales agreements and price adjustments' },
  { id: 'Buyer Receivables', title: 'Buyer Receivables Aging', category: 'Sales', desc: 'Outstanding balances on vehicle sales' },
  { id: 'Customer Garage Receivables', title: 'Customer Garage Receivables', category: 'Operations', desc: 'Unpaid customer repair and service invoices' },
  { id: 'Running Capital', title: 'Running Capital Ledger', category: 'Accounting', desc: 'Vehicle-linked company capital and recoveries' },
  { id: 'Company Result', title: 'Operational Cash Result', category: 'Financial', desc: 'Operating cash flow and margin components' },
  { id: 'Owner Distribution', title: 'Owner Distribution (BDR)', category: 'Governance', desc: 'Unapproved drawings policy and governance' },
];

export const ReportShell: React.FC<ReportShellProps> = ({
  activeRoute,
  data,
  garages,
  selectedGarage,
  onSelectGarage,
  onSelectRoute,
}) => {
  const isDirectory = activeRoute === 'All Reports' || activeRoute === 'Reports';
  const [searchQuery, setSearchQuery] = useState('');
  const [activeReportKey, setActiveReportKey] = useState<string>(
    isDirectory ? 'Company Consolidated' : activeRoute
  );

  const currentReportKey = isDirectory ? activeReportKey : activeRoute;
  const reportDef: ReportDefinition = getReportData(currentReportKey, data, selectedGarage);

  const formatValue = (val: any, format?: string) => {
    if (val === undefined || val === null) return '—';
    if (format === 'currency') {
      return typeof val === 'number' ? '₹' + Math.round(val).toLocaleString('en-IN') : val;
    }
    if (format === 'number') {
      return typeof val === 'number' ? val.toLocaleString('en-IN') : val;
    }
    return String(val);
  };

  const filteredRows = reportDef.rows.filter((row) => {
    if (!searchQuery.trim()) return true;
    return Object.values(row).some((val) =>
      String(val).toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="space-y-4 sm:space-y-5 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-[#f2ebe5] dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">
            REPORTS & ANALYTICS
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            {reportDef.name}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium">
            {reportDef.description}
          </p>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Garage Selector */}
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

          <button
            onClick={() => window.print()}
            title="Print report"
            className="w-8 h-8 rounded-full bg-white dark:bg-zinc-800 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50 flex items-center justify-center text-gray-600 dark:text-gray-300 transition cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Report Switcher Pills (If in Directory mode) */}
      {isDirectory && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {ALL_REPORT_CARDS.map((r) => (
            <button
              key={r.id}
              onClick={() => setActiveReportKey(r.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                activeReportKey === r.id
                  ? 'bg-[#18181b] text-white shadow-2xs'
                  : 'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50'
              }`}
            >
              {r.title}
            </button>
          ))}
        </div>
      )}

      {/* KPI Cards (if present in report) */}
      {reportDef.summary && reportDef.summary.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {reportDef.summary.map((card, idx) => (
            <div
              key={idx}
              className={`rounded-[24px] p-3.5 px-4 flex flex-col justify-between min-h-[80px] ${
                idx === 0
                  ? 'dashboard-card-orange text-white shadow-xs'
                  : 'dashboard-card-solid'
              }`}
            >
              <span
                className={`text-[11px] font-medium leading-none ${
                  idx === 0 ? 'text-white/90' : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                {card.label}
              </span>
              <span
                className={`text-xl sm:text-2xl font-bold tracking-tight my-auto ${
                  idx === 0 ? 'text-white' : 'text-gray-950 dark:text-white'
                }`}
              >
                {card.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Report Table Card */}
      <div className="dashboard-card-solid rounded-[24px] overflow-hidden">
        {/* Table Search & Tools */}
        <div className="p-4 px-5 border-b border-[#f0e7df] dark:border-zinc-800 flex items-center justify-between gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder={`Search ${reportDef.name.toLowerCase()}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-full text-xs bg-gray-50 dark:bg-zinc-800/60 border border-[#e2d8ce] dark:border-zinc-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary)]"
            />
          </div>

          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">
            {filteredRows.length} record{filteredRows.length !== 1 ? 's' : ''} in view
          </div>
        </div>

        {/* High-density Data Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#f0e7df] dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/30">
                {reportDef.columns.map((col) => (
                  <th
                    key={col.key}
                    className={`py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider ${
                      col.align === 'right'
                        ? 'text-right'
                        : col.align === 'center'
                        ? 'text-center'
                        : 'text-left'
                    }`}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f5ede5] dark:divide-zinc-800/60">
              {filteredRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={reportDef.columns.length}
                    className="py-12 text-center text-xs text-gray-500 dark:text-gray-400 font-medium"
                  >
                    No matching records found.
                  </td>
                </tr>
              ) : (
                filteredRows.map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    className="hover:bg-gray-50/70 dark:hover:bg-zinc-800/40 transition-colors"
                  >
                    {reportDef.columns.map((col) => (
                      <td
                        key={col.key}
                        className={`py-3 px-4 font-medium text-gray-900 dark:text-gray-100 ${
                          col.align === 'right'
                            ? 'text-right font-mono font-semibold'
                            : col.align === 'center'
                            ? 'text-center'
                            : 'text-left'
                        }`}
                      >
                        {formatValue(row[col.key], col.format)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
