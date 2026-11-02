import React, { useState, useRef, useEffect } from 'react';
import {
  ArrowLeft,
  Wrench,
  Plus,
  CheckCircle2,
  Clock,
  ChevronDown,
  Building2,
  Check,
  RotateCcw,
  Receipt,
  DollarSign,
  FileText,
} from 'lucide-react';
import { Job, Vehicle, Garage, Data } from '../types';
import { useCanPresentBusinessWriteActions } from '../auth/RolePresentationContext';
import { getFormDataSourceStatus } from '../data/navigationRegistry';
import { DemoBadge } from './shared/DemoBadge';
import { capitalContribution } from '../utils/selectors';

interface GarageJobDetailViewProps {
  job: Job;
  vehicle: Vehicle;
  garages: Garage[];
  data?: Data;
  selectedGarage: string;
  onSelectGarage: (garageId: string) => void;
  onBack: () => void;
  backLabel?: string;
  onAddWork?: (job: Job) => void;
  onAddCostOrCharge?: (job: Job) => void;
  onReceive?: (job: Job) => void;
  onToggleJobStatus?: (job: Job) => void;
}

export const GarageJobDetailView: React.FC<GarageJobDetailViewProps> = ({
  job,
  vehicle,
  garages,
  data,
  selectedGarage,
  onSelectGarage,
  onBack,
  backLabel = 'Back to Garage Jobs',
  onAddWork,
  onAddCostOrCharge,
  onReceive,
  onToggleJobStatus,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const [isGarageDropdownOpen, setIsGarageDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsGarageDropdownOpen(false);
      }
    };
    if (isGarageDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isGarageDropdownOpen]);

  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    return '₹' + val.toLocaleString('en-IN');
  };

  const isCustomer = vehicle.type === 'Customer';
  const outstanding = Math.max(0, job.charge - job.received);
  const totalCosts = (job.costs ?? []).reduce((acc, c) => acc + c.amount, 0);
  const runningCapital = data ? capitalContribution(data, vehicle.id) : 0;

  // Active garage calculation: either from global selection, or from job.garageId
  const activeGarageId = selectedGarage !== 'all' ? selectedGarage : job.garageId;
  const currentGarage = garages.find((g) => g.id === activeGarageId) || garages[0];

  return (
    <div className="space-y-4 sm:space-y-5">
      {/* Top Breadcrumb & Action Row */}
      <div className="flex items-center justify-between gap-3">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-gray-600 dark:text-gray-300 hover:text-[var(--theme-primary)] transition-colors group cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" />
          <span>{backLabel}</span>
        </button>

        <div className="flex items-center gap-2">
          {canPresentWriteActions && onToggleJobStatus && (
            <button
              onClick={() => onToggleJobStatus(job)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors shadow-xs cursor-pointer"
            >
              {job.status === 'Open' ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Mark completed</span>
                  {getFormDataSourceStatus('job') === 'demo' && <DemoBadge size="compact" />}
                </>
              ) : (
                <>
                  <RotateCcw className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
                  <span>Reopen job</span>
                  {getFormDataSourceStatus('job') === 'demo' && <DemoBadge size="compact" />}
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Page Title & Vehicle Info Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold tracking-wider text-[var(--theme-primary)] uppercase">
              GARAGE JOB
            </span>
            <span className="text-gray-300 dark:text-gray-600">·</span>
            <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400">
              {job.number}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            {job.number} · {job.description}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="font-semibold text-gray-700 dark:text-gray-300">{vehicle.number}</span>
            <span>·</span>
            <span>{vehicle.model}</span>
            <span>·</span>
            <span>{isCustomer ? 'Customer' : 'Investor'}: {vehicle.person}</span>
            <span>·</span>
            <span>{currentGarage?.name ?? 'Central Garage'}</span>
            <span>·</span>
            <span>{job.date}</span>
          </p>
        </div>

        {/* Action Button Row */}
        <div className="flex items-center gap-2 flex-wrap">
          {canPresentWriteActions && onAddWork && (
            <button
              onClick={() => onAddWork(job)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-750 text-gray-800 dark:text-gray-200 transition-colors shadow-xs cursor-pointer"
            >
              <Wrench className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              <span>Add work</span>
              {getFormDataSourceStatus('jobWork') === 'demo' && <DemoBadge size="compact" />}
            </button>
          )}

          {isCustomer ? (
            <>
              {canPresentWriteActions && onAddCostOrCharge && (
                <button
                  onClick={() => onAddCostOrCharge(job)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-750 text-gray-800 dark:text-gray-200 transition-colors shadow-xs cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  <span>Add charge</span>
                  {getFormDataSourceStatus('customerCharge') === 'demo' && <DemoBadge size="compact" />}
                </button>
              )}
              {canPresentWriteActions && outstanding > 0 && onReceive && (
                <button
                  onClick={() => onReceive(job)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-[var(--theme-primary)] hover:brightness-110 text-white transition-all shadow-md shadow-[var(--theme-accent-shadow)] cursor-pointer"
                >
                  <Receipt className="w-3.5 h-3.5 text-white" />
                  <span>Receive</span>
                  {getFormDataSourceStatus('customerReceipt') === 'demo' && <DemoBadge size="compact" />}
                </button>
              )}
            </>
          ) : (
            canPresentWriteActions && onAddCostOrCharge && (
              <button
                onClick={() => onAddCostOrCharge(job)}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-[var(--theme-primary)] hover:brightness-110 text-white transition-all shadow-md shadow-[var(--theme-accent-shadow)] cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5 text-white" />
                <span>Add cost</span>
                {getFormDataSourceStatus('jobExpense') === 'demo' && <DemoBadge size="compact" />}
              </button>
            )
          )}
        </div>
      </div>

      {/* TOP SECTION: Summary Cards Row (matching Ember Tablet layout) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-3.5 items-stretch">
        {/* CARD 1: Orange Garage Selector Dropdown Card */}
        <div ref={dropdownRef} className="relative min-w-0">
          <div
            onClick={() => setIsGarageDropdownOpen((prev) => !prev)}
            className="dashboard-card-orange rounded-[24px] min-h-[96px] sm:min-h-[102px] p-4 px-5 sm:px-6 text-white shadow-xs hover:brightness-105 transition-all flex flex-col justify-center items-start text-left cursor-pointer select-none group"
            title="Click to change active garage"
          >
            {/* Top Row: Label */}
            <div className="flex items-center justify-between w-full mb-1">
              <span className="flex items-center gap-1.5 text-[11px] font-normal text-white/85 tracking-normal">
                <Building2 className="w-3.5 h-3.5 text-white/80" />
                <span>Assigned Garage</span>
              </span>
              <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center shrink-0 transition-transform duration-200">
                <ChevronDown
                  className={`w-3 h-3 text-white transition-transform duration-200 ${
                    isGarageDropdownOpen ? 'rotate-180' : ''
                  }`}
                />
              </div>
            </div>

            {/* Center: Garage Name */}
            <div className="text-lg sm:text-xl font-semibold text-white tracking-tight truncate w-full">
              {currentGarage?.name ?? 'Central Garage'}
            </div>

            {/* Bottom Row: Location Info */}
            <div className="text-[11px] text-white/80 font-normal mt-1 truncate">
              {currentGarage?.location ? `${currentGarage.location} Facility` : 'Active Garage'}
            </div>
          </div>

          {/* Expanded Garage Dropdown Popover */}
          {isGarageDropdownOpen && (
            <div
              data-testid="garage-dropdown-menu"
              className="absolute top-[calc(100%+8px)] left-0 w-full min-w-[240px] z-50 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl p-2 max-h-64 overflow-y-auto space-y-1 animate-in fade-in zoom-in-95 duration-150"
            >
              <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                Select Active Branch ({garages.length} available)
              </div>
              {garages.map((garage) => {
                const isSelected = garage.id === currentGarage?.id;
                return (
                  <button
                    key={garage.id}
                    onClick={() => {
                      onSelectGarage(garage.id);
                      setIsGarageDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between transition-colors cursor-pointer ${
                      isSelected
                        ? 'bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] font-bold border border-[var(--theme-primary-border)]'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    <div>
                      <div className="font-semibold">{garage.name}</div>
                      <div className="text-[10px] text-gray-500 dark:text-gray-400">
                        {garage.location}
                      </div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-[var(--theme-primary)]" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* CARD 2: Job Status Card */}
        <div className="dashboard-card-solid rounded-[24px] min-h-[96px] sm:min-h-[102px] p-4 px-5 sm:px-6 flex flex-col justify-center items-start text-left shadow-xs border border-gray-200/80 dark:border-gray-800/80">
          <div className="text-xs font-normal text-gray-500 dark:text-gray-400 tracking-normal mb-1.5 text-left">
            Job Status
          </div>
          <div className="flex items-center justify-start">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                job.status === 'Open'
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60'
                  : 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800/60'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  job.status === 'Open' ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500'
                }`}
              />
              {job.status}
            </span>
          </div>
          <div className="text-[11px] text-left text-gray-400 dark:text-gray-500 font-normal mt-1.5">
            {job.workEntries?.length ?? 0} work entries logged
          </div>
        </div>

        {/* CARD 3: Financial Metric 1 (Charges or Job Costs) */}
        <div className="dashboard-card-solid rounded-[24px] min-h-[96px] sm:min-h-[102px] p-4 px-5 sm:px-6 flex flex-col justify-center items-start text-left shadow-xs border border-gray-200/80 dark:border-gray-800/80">
          <div className="text-xs font-normal text-gray-500 dark:text-gray-400 tracking-normal mb-1 text-left">
            {isCustomer ? 'Charges' : 'Job Costs'}
          </div>
          <div className="text-2xl sm:text-[26px] font-semibold text-gray-900 dark:text-white tracking-tight leading-none text-left">
            {isCustomer ? formatCurrency(job.charge) : formatCurrency(totalCosts)}
          </div>
          <div className="text-[11px] text-left text-gray-400 dark:text-gray-500 font-normal mt-1.5 leading-none">
            {isCustomer ? 'Total invoice amount' : 'Parts, labour & materials'}
          </div>
        </div>

        {/* CARD 4: Financial Metric 2 (Outstanding or Running Capital) - Centered Vertically, Left-Aligned, Balanced Weight */}
        <div className="dashboard-card-solid rounded-[24px] min-h-[96px] sm:min-h-[102px] p-4 px-5 sm:px-6 flex flex-col justify-center items-start text-left shadow-xs border border-gray-200/80 dark:border-gray-800/80">
          <div className="text-xs font-normal text-gray-500 dark:text-gray-400 tracking-normal mb-1 text-left">
            {isCustomer ? 'Outstanding' : 'Company Running Capital'}
          </div>
          <div className="text-2xl sm:text-[26px] font-semibold text-gray-900 dark:text-white tracking-tight leading-none text-left">
            {isCustomer ? formatCurrency(outstanding) : formatCurrency(runningCapital)}
          </div>
          <div className="text-[11px] text-left text-gray-400 dark:text-gray-500 font-normal mt-1.5 leading-none">
            {isCustomer
              ? outstanding > 0
                ? 'Pending customer settlement'
                : 'Settled in full'
              : 'Vehicle capital contribution'}
          </div>
        </div>
      </div>

      {/* MAIN CONTENT AREA: Clean Table Panels (Ember Reference Table Aesthetic) */}
      <div className="dashboard-card-solid rounded-[28px] p-5 sm:p-7 shadow-xs border border-gray-200/80 dark:border-gray-800/80 space-y-6">
        {/* Section 1: Work Log Table */}
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                Work Log
              </h2>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-semibold">
                {job.workEntries?.length ?? 0}
              </span>
            </div>
            {canPresentWriteActions && onAddWork && (
              <button
                onClick={() => onAddWork(job)}
                className="text-xs font-semibold text-[var(--theme-primary)] hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add work entry</span>
                {getFormDataSourceStatus('jobWork') === 'demo' && <DemoBadge size="compact" />}
              </button>
            )}
          </div>

          <div className="overflow-x-auto mt-2">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-800 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Type / Category</th>
                  <th className="py-2.5 px-3">Work Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {(job.workEntries ?? []).map((w) => (
                  <tr key={w.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition-colors">
                    <td className="py-3 px-3 font-medium text-gray-600 dark:text-gray-300 whitespace-nowrap">
                      {w.date}
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-semibold text-[11px]">
                        {w.category}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-medium text-gray-900 dark:text-white">
                      {w.description}
                    </td>
                  </tr>
                ))}
                {(!job.workEntries || job.workEntries.length === 0) && (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-xs text-gray-400 dark:text-gray-500">
                      No work entries recorded. Use "+ Add work" to record labor and maintenance.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 2: Financial Table (Customer Charges/Receipts OR Stock Vehicle Costs) */}
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                {isCustomer ? 'Customer Charges & Receipts' : 'Stock Vehicle Costs'}
              </h2>
            </div>
            {canPresentWriteActions && onAddCostOrCharge && (
              <button
                onClick={() => onAddCostOrCharge(job)}
                className="text-xs font-semibold text-[var(--theme-primary)] hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{isCustomer ? 'Add charge' : 'Add cost'}</span>
                {getFormDataSourceStatus(isCustomer ? 'customerCharge' : 'jobExpense') === 'demo' && <DemoBadge size="compact" />}
              </button>
            )}
          </div>

          <div className="overflow-x-auto mt-2">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-800 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                  {isCustomer ? (
                    <>
                      <th className="py-2.5 px-3">Type / Date</th>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3 text-right">Amount</th>
                    </>
                  ) : (
                    <>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3 text-right">Cost</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {isCustomer ? (
                  <>
                    {(job.charges ?? []).map((c) => (
                      <tr key={c.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition-colors">
                        <td className="py-3 px-3 whitespace-nowrap">
                          <div className="font-semibold text-gray-800 dark:text-gray-200">{c.category}</div>
                          <div className="text-[10px] text-gray-400">{c.date}</div>
                        </td>
                        <td className="py-3 px-3 text-gray-700 dark:text-gray-300 font-medium">
                          {c.description}
                        </td>
                        <td className="py-3 px-3 text-right font-bold text-gray-900 dark:text-white">
                          {formatCurrency(c.amount)}
                        </td>
                      </tr>
                    ))}
                    {job.received > 0 && (
                      <tr className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition-colors bg-emerald-50/30 dark:bg-emerald-950/10">
                        <td className="py-3 px-3 whitespace-nowrap">
                          <div className="font-semibold text-emerald-700 dark:text-emerald-400">
                            Actual Receipt
                          </div>
                          <div className="text-[10px] text-gray-400">{job.date}</div>
                        </td>
                        <td className="py-3 px-3 text-gray-700 dark:text-gray-300 font-medium">
                          Customer collection / payment on account
                        </td>
                        <td className="py-3 px-3 text-right font-bold text-emerald-600 dark:text-emerald-400">
                          - {formatCurrency(job.received)}
                        </td>
                      </tr>
                    )}
                    {(!job.charges || job.charges.length === 0) && job.received === 0 && (
                      <tr>
                        <td colSpan={3} className="py-6 text-center text-xs text-gray-400 dark:text-gray-500">
                          No charges or actual receipts recorded yet.
                        </td>
                      </tr>
                    )}
                  </>
                ) : (
                  <>
                    {(job.costs ?? []).map((c) => (
                      <tr key={c.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition-colors">
                        <td className="py-3 px-3 whitespace-nowrap font-medium text-gray-600 dark:text-gray-300">
                          {c.date}
                        </td>
                        <td className="py-3 px-3 text-gray-700 dark:text-gray-300 font-medium">
                          {c.description}
                        </td>
                        <td className="py-3 px-3 text-right font-bold text-gray-900 dark:text-white">
                          {formatCurrency(c.amount)}
                        </td>
                      </tr>
                    ))}
                    {(!job.costs || job.costs.length === 0) && (
                      <tr>
                        <td colSpan={3} className="py-6 text-center text-xs text-gray-400 dark:text-gray-500">
                          No stock vehicle costs recorded for this job.
                        </td>
                      </tr>
                    )}
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 3: Status History (if present) */}
        {job.statusHistory && job.statusHistory.length > 0 && (
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
              <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                Status History
              </h2>
            </div>
            <div className="overflow-x-auto mt-2">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-gray-100 dark:border-gray-800 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                    <th className="py-2.5 px-3">Time</th>
                    <th className="py-2.5 px-3">Change</th>
                    <th className="py-2.5 px-3">Actor</th>
                    <th className="py-2.5 px-3">Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {job.statusHistory.map((h) => (
                    <tr key={h.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition-colors">
                      <td className="py-3 px-3 font-medium text-gray-600 dark:text-gray-300 whitespace-nowrap">
                        {h.timestamp}
                      </td>
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-semibold text-[11px]">
                          {h.from} → {h.to}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-gray-800 dark:text-gray-200 font-medium">
                        {h.actor}
                      </td>
                      <td className="py-3 px-3 text-gray-500 dark:text-gray-400">
                        {h.note}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
