import React, { useState } from 'react';
import {
  Search,
  Plus,
  Wrench,
  CheckCircle2,
  RotateCcw,
  Receipt,
  Car,
  ChevronRight,
} from 'lucide-react';
import { Job, Vehicle, Garage } from '../types';
import { useCanPresentBusinessWriteActions } from '../auth/RolePresentationContext';

interface GarageJobsViewProps {
  jobs: Job[];
  vehicles: Vehicle[];
  garages: Garage[];
  selectedGarage: string;
  onSelectJob: (job: Job) => void;
  onNewJob: () => void;
  onAddWork: (job: Job) => void;
  onAddCostOrCharge: (job: Job) => void;
  onReceive?: (job: Job) => void;
  onToggleStatus: (job: Job) => void;
}

export const GarageJobsView: React.FC<GarageJobsViewProps> = ({
  jobs,
  vehicles,
  garages,
  selectedGarage,
  onSelectJob,
  onNewJob,
  onAddWork,
  onAddCostOrCharge,
  onReceive,
  onToggleStatus,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const [searchTerm, setSearchTerm] = useState('');

  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    return '₹' + val.toLocaleString('en-IN');
  };

  // Filter jobs by selected garage and search term
  const filteredJobs = jobs.filter((j) => {
    if (selectedGarage !== 'all' && j.garageId !== selectedGarage) return false;
    if (!searchTerm.trim()) return true;

    const term = searchTerm.toLowerCase();
    const vehicle = vehicles.find((v) => v.id === j.vehicleId);
    return (
      j.number.toLowerCase().includes(term) ||
      j.description.toLowerCase().includes(term) ||
      (vehicle?.number.toLowerCase().includes(term) ?? false) ||
      (vehicle?.model.toLowerCase().includes(term) ?? false) ||
      (vehicle?.person.toLowerCase().includes(term) ?? false)
    );
  });

  // KPI Metrics calculated from real active jobs data (Ember Quotes Reference Layout)
  const totalCharges = filteredJobs.reduce((acc, j) => acc + (j.charge || 0), 0);
  const completedCount = filteredJobs.filter((j) => j.status === 'Completed').length;
  const openCount = filteredJobs.filter((j) => j.status === 'Open').length;
  const totalOutstanding = filteredJobs.reduce((acc, j) => {
    const vehicle = vehicles.find((v) => v.id === j.vehicleId);
    if (vehicle?.type === 'Customer') {
      return acc + Math.max(0, (j.charge || 0) - (j.received || 0));
    }
    return acc;
  }, 0);

  return (
    <div className="space-y-4 sm:space-y-5">
      {/* Header Area (matching Ember Reference Header + Pill Action) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1">
        <div>
          <div className="text-[11px] font-bold tracking-wider text-[var(--theme-primary)] uppercase">
            GARAGE OPERATIONS
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            Garage Jobs
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Shared synthetic data across vehicles, jobs, inventory and accounting.
          </p>
        </div>

        {canPresentWriteActions && <button
          onClick={onNewJob}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold rounded-full bg-[var(--theme-primary)] hover:brightness-110 text-white transition-all shadow-md shadow-[var(--theme-accent-shadow)] cursor-pointer self-start sm:self-auto shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New job</span>
        </button>}
      </div>

      {/* 3 Summary KPI Cards (matching Ember Quotes 3-Card Header Aesthetic & Image 3 Alignment) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 items-stretch">
        {/* CARD 1: Solid Accent Card (Total Charges / Quoted) */}
        <div className="dashboard-card-orange rounded-[24px] min-h-[96px] sm:min-h-[104px] p-4 px-5 sm:px-6 flex flex-col justify-center items-start text-left shadow-xs select-none">
          <div className="text-xs font-normal text-white/85 tracking-normal mb-1 text-left">
            Total Charges
          </div>
          <div className="text-2xl sm:text-3xl font-semibold text-white tracking-tight leading-none text-left">
            {formatCurrency(totalCharges)}
          </div>
          <div className="text-[11px] text-white/80 font-normal mt-1.5 leading-none text-left">
            {filteredJobs.length} total jobs logged
          </div>
        </div>

        {/* CARD 2: Solid White Card (Completed Jobs) */}
        <div className="dashboard-card-solid rounded-[24px] min-h-[96px] sm:min-h-[104px] p-4 px-5 sm:px-6 flex flex-col justify-center items-start text-left shadow-xs border border-gray-200/80 dark:border-gray-800/80 select-none">
          <div className="text-xs font-normal text-gray-500 dark:text-gray-400 tracking-normal mb-1 text-left">
            Completed Jobs
          </div>
          <div className="text-2xl sm:text-3xl font-semibold text-gray-950 dark:text-white tracking-tight leading-none text-left">
            {completedCount} {completedCount === 1 ? 'Job' : 'Jobs'}
          </div>
          <div className="text-[11px] text-gray-400 dark:text-gray-500 font-normal mt-1.5 leading-none text-left">
            {openCount} active in progress
          </div>
        </div>

        {/* CARD 3: Solid White Card (Outstanding Due) */}
        <div className="dashboard-card-solid rounded-[24px] min-h-[96px] sm:min-h-[104px] p-4 px-5 sm:px-6 flex flex-col justify-center items-start text-left shadow-xs border border-gray-200/80 dark:border-gray-800/80 select-none">
          <div className="text-xs font-normal text-gray-500 dark:text-gray-400 tracking-normal mb-1 text-left">
            Outstanding Due
          </div>
          <div className="text-2xl sm:text-3xl font-semibold text-gray-950 dark:text-white tracking-tight leading-none text-left">
            {formatCurrency(totalOutstanding)}
          </div>
          <div className="text-[11px] text-gray-400 dark:text-gray-500 font-normal mt-1.5 leading-none text-left">
            Pending customer settlement
          </div>
        </div>
      </div>

      {/* Main Work Queue Panel */}
      <div className="dashboard-card-solid rounded-[26px] p-5 sm:p-6 shadow-xs border border-gray-200/80 dark:border-gray-800/80 space-y-4">
        {/* Panel Top: Title and Description */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-gray-100 dark:border-gray-800">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
              Garage work queue
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Search an existing vehicle. Garage Jobs never register a Vehicle.
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search job, vehicle or customer"
            className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-hidden focus:ring-2 focus:ring-[var(--theme-primary-border)] focus:border-[var(--theme-primary)] transition-all"
          />
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                <th className="py-3 px-3">Job / Vehicle</th>
                <th className="py-3 px-3">Garage</th>
                <th className="py-3 px-3">Customer / Investor</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Charges / Outstanding</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {filteredJobs.map((j) => {
                const vehicle = vehicles.find((v) => v.id === j.vehicleId);
                const garage = garages.find((g) => g.id === j.garageId);
                const isCustomer = vehicle?.type === 'Customer';
                const due = Math.max(0, j.charge - j.received);
                const totalCosts = (j.costs ?? []).reduce((acc, c) => acc + c.amount, 0);

                return (
                  <tr
                    key={j.id}
                    className="hover:bg-gray-50/70 dark:hover:bg-gray-800/40 transition-colors group"
                  >
                    {/* Job / Vehicle */}
                    <td className="py-3.5 px-3 min-w-[200px]">
                      <div className="font-bold text-gray-950 dark:text-white flex items-center gap-1.5">
                        <span>{j.number}</span>
                        <span>·</span>
                        <span className="truncate">{j.description}</span>
                      </div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 flex items-center gap-1">
                        <Car className="w-3 h-3 text-gray-400 shrink-0" />
                        <span className="font-medium text-gray-700 dark:text-gray-300">
                          {vehicle?.number ?? 'Vehicle'}
                        </span>
                        <span>·</span>
                        <span>{vehicle?.model ?? ''}</span>
                      </div>
                    </td>

                    {/* Garage */}
                    <td className="py-3.5 px-3 whitespace-nowrap text-gray-700 dark:text-gray-300 font-medium">
                      {garage?.name ?? '—'}
                    </td>

                    {/* Customer / Investor */}
                    <td className="py-3.5 px-3 whitespace-nowrap text-gray-700 dark:text-gray-300 font-medium">
                      {isCustomer ? vehicle?.person ?? 'Customer' : 'Stock / Investor'}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      {canPresentWriteActions ? <button
                        onClick={() => onToggleStatus(j)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-colors cursor-pointer ${
                          j.status === 'Open'
                            ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/60 hover:bg-emerald-100'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-200'
                        }`}
                        title="Click to toggle status"
                      >
                        {j.status === 'Open' ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                            <span>Mark completed</span>
                          </>
                        ) : (
                          <>
                            <RotateCcw className="w-3 h-3 text-gray-500" />
                            <span>Reopen</span>
                          </>
                        )}
                      </button> : <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{j.status}</span>}
                    </td>

                    {/* Charges / Outstanding */}
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <div className="font-bold text-gray-900 dark:text-white">
                        {formatCurrency(j.charge)}
                      </div>
                      <div className="text-[10px] text-gray-500 dark:text-gray-400">
                        {isCustomer
                          ? `${formatCurrency(due)} outstanding`
                          : `Costs ${formatCurrency(totalCosts)}`}
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-3 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-2">
                        {canPresentWriteActions && <>
                        <button
                          onClick={() => onSelectJob(j)}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] hover:brightness-95 transition-colors inline-flex items-center gap-0.5 cursor-pointer"
                        >
                          <span>Details</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => onAddWork(j)}
                          className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors cursor-pointer"
                        >
                          Add work
                        </button>
                        {isCustomer ? (
                          <>
                            <button
                              onClick={() => onAddCostOrCharge(j)}
                              className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors cursor-pointer"
                            >
                              Add charge
                            </button>
                            {due > 0 && onReceive && (
                              <button
                                onClick={() => onReceive(j)}
                                className="text-xs font-semibold text-[var(--theme-primary)] hover:underline cursor-pointer"
                              >
                                Receive
                              </button>
                            )}
                          </>
                        ) : (
                          <button
                            onClick={() => onAddCostOrCharge(j)}
                            className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors cursor-pointer"
                          >
                            Add cost
                          </button>
                        )}
                        </>}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {filteredJobs.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-gray-400 dark:text-gray-500">
                    No garage jobs match this filter. Create one from an existing vehicle.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
