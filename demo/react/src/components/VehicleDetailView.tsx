import React from 'react';
import { ArrowLeft, Plus, Wrench, DollarSign, Calendar, MapPin, Layers } from 'lucide-react';
import { Vehicle, Garage, Job, Data } from '../types';
import { VehicleImageCard } from './VehicleImageCard';
import { capitalContribution, totalVehicleCost } from '../utils/selectors';
import { useCanPresentBusinessWriteActions } from '../auth/RolePresentationContext';

interface VehicleDetailViewProps {
  vehicle: Vehicle;
  garages: Garage[];
  jobs: Job[];
  data?: Data;
  onBack: () => void;
  onCreateJob: (vehicle: Vehicle) => void;
  onAddExpense: (vehicle: Vehicle) => void;
  onViewJobDetail?: (job: Job) => void;
}

export const VehicleDetailView: React.FC<VehicleDetailViewProps> = ({
  vehicle,
  garages,
  jobs,
  data,
  onBack,
  onCreateJob,
  onAddExpense,
  onViewJobDetail,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    return '₹' + val.toLocaleString('en-IN');
  };

  const currentGarage = garages.find((g) => g.id === vehicle.garageId);
  const garageName = currentGarage ? currentGarage.name : 'Central Garage';

  // Filter jobs for this specific vehicle
  const vehicleJobs = jobs.filter((j) => j.vehicleId === vehicle.id);

  // Capital contribution / outstanding
  const isCustomer = vehicle.type === 'Customer';
  const customerOutstanding = vehicleJobs.reduce(
    (acc, j) => acc + Math.max(0, j.charge - j.received),
    0
  );
  const runningCapital = data ? capitalContribution(data, vehicle.id) : 0;
  const currentVehicleCost = data
    ? totalVehicleCost(data, vehicle.id)
    : (vehicle.totalCost ?? vehicle.purchase);

  return (
    <div className="flex flex-col gap-4 animate-in fade-in duration-150">
      {/* 1. Back to Vehicles Navigation */}
      <div>
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-600 hover:text-black dark:text-gray-400 dark:hover:text-white transition cursor-pointer group py-1"
        >
          <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
          <span>Back to Vehicles</span>
        </button>
      </div>

      {/* 2. Heading Section matching IMAGE 2 */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-1 border-b border-[#f2ebe5] dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">
            VEHICLE WORKSPACE
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            {vehicle.model} <span className="opacity-40 font-normal">·</span> {vehicle.number}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-medium">
            {isCustomer ? 'Customer' : 'Investor'} · {vehicle.person} · Current garage: {garageName}
          </p>
        </div>

        {/* Action Buttons matching IMAGE 2 */}
        {canPresentWriteActions && (
        <div className="flex items-center gap-2">
          <button
            onClick={() => onCreateJob(vehicle)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-white dark:bg-zinc-800 hover:bg-gray-50 dark:hover:bg-zinc-700 text-gray-900 dark:text-white border border-[#e2d8ce] dark:border-zinc-700 text-xs font-bold shadow-2xs transition cursor-pointer active:scale-95"
          >
            <Plus className="w-3.5 h-3.5 text-gray-500" />
            <span>Create Garage Job</span>
          </button>

          {!isCustomer && (
            <button
              onClick={() => onAddExpense(vehicle)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-[#18181b] hover:bg-black text-white text-xs font-bold shadow-xs transition cursor-pointer active:scale-95"
            >
              <Plus className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
              <span>Add Expense</span>
            </button>
          )}
        </div>
        )}
      </div>

      {/* 3. Top Summary Row: Tablet Reference Style (Reduced Height ~88px, Increased Side Curves rounded-[26px]) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-stretch">
        {/* Card 1: Vehicle cost (Signature Orange Card matching Reference Image) */}
        <div className="dashboard-card-orange text-white rounded-[26px] px-4 sm:px-5 py-2.5 flex flex-col justify-between min-h-[84px] max-h-[96px] shadow-xs">
          <div className="w-full text-left leading-none">
            <span className="text-[11px] font-medium text-white/90">
              Vehicle cost
            </span>
          </div>
          <div className="my-auto flex items-center justify-start text-left text-2xl sm:text-[27px] font-bold text-white tracking-tight">
            {formatCurrency(currentVehicleCost)}
          </div>
        </div>

        {/* Card 2: Company Running Capital or Customer outstanding */}
        <div className="dashboard-card-solid rounded-[26px] px-4 sm:px-5 py-2.5 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <div className="w-full text-left leading-none">
            <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400">
              {isCustomer ? 'Customer outstanding' : 'Company Running Capital'}
            </span>
          </div>
          <div className="my-auto flex items-center justify-start text-left text-2xl sm:text-[27px] font-bold text-gray-950 dark:text-white tracking-tight">
            {formatCurrency(isCustomer ? customerOutstanding : runningCapital)}
          </div>
        </div>

        {/* Card 3: Garage jobs */}
        <div className="dashboard-card-solid rounded-[26px] px-4 sm:px-5 py-2.5 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <div className="w-full text-left leading-none">
            <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400">
              Garage jobs
            </span>
          </div>
          <div className="my-auto flex items-center justify-start text-left text-2xl sm:text-[27px] font-bold text-gray-950 dark:text-white tracking-tight">
            {vehicleJobs.length}
          </div>
        </div>

        {/* Card 4: Status */}
        <div className="dashboard-card-solid rounded-[26px] px-4 sm:px-5 py-2.5 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <div className="w-full text-left leading-none">
            <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400">
              Status
            </span>
          </div>
          <div className="my-auto flex items-center justify-start gap-2 text-left text-xl sm:text-2xl font-bold text-gray-950 dark:text-white tracking-tight">
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                vehicle.status === 'In work'
                  ? 'bg-amber-500 animate-pulse'
                  : vehicle.status === 'Sold'
                  ? 'bg-gray-400'
                  : vehicle.status === 'Purchased'
                  ? 'bg-blue-500'
                  : 'bg-emerald-500'
              }`}
            />
            <span className="truncate">{vehicle.status}</span>
          </div>
        </div>

        {/* Card 5: Dedicated Landscape Vehicle Image Slot (Aligned to same height & curve) */}
        <VehicleImageCard
          imageUrl={vehicle.imageUrl}
          altText={`${vehicle.model} - ${vehicle.number}`}
        />
      </div>

      {/* 4. Lower Section: Garage History Panel matching IMAGE 2 */}
      <div className="dashboard-card-solid rounded-[22px] p-4 sm:p-5 flex flex-col gap-3.5">
        <div className="flex items-center justify-between pb-2.5 border-b border-[#f2ebe5] dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <h2 className="text-sm sm:text-base font-bold text-gray-950 dark:text-white">
              Garage history
            </h2>
            <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-zinc-800 text-[10px] font-bold text-gray-600 dark:text-gray-300">
              {vehicleJobs.length} {vehicleJobs.length === 1 ? 'job' : 'jobs'}
            </span>
          </div>

          {canPresentWriteActions && <button
            onClick={() => onCreateJob(vehicle)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-white dark:bg-zinc-800 hover:bg-gray-50 dark:hover:bg-zinc-700 text-gray-800 dark:text-gray-200 border border-[#e2d8ce] dark:border-zinc-700 text-xs font-bold shadow-2xs transition cursor-pointer active:scale-95"
          >
            <Plus className="w-3 h-3 text-[var(--theme-primary)]" />
            <span>Add job</span>
          </button>}
        </div>

        {/* Jobs List or Empty State */}
        {vehicleJobs.length > 0 ? (
          <div className="flex flex-col gap-2">
            {vehicleJobs.map((job) => {
              const jobGarage = garages.find((g) => g.id === job.garageId)?.name || 'Central Garage';
              return (
                <div
                  key={job.id}
                  className="bg-white dark:bg-zinc-800/80 border border-[#eee6de] dark:border-zinc-700/70 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 hover:border-[var(--theme-primary-border)] dark:hover:border-zinc-600 transition"
                >
                  <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-extrabold text-gray-950 dark:text-white">
                        {job.number}
                      </span>
                      <span className="text-xs opacity-40 font-normal">·</span>
                      <span className="text-xs font-bold text-gray-800 dark:text-gray-200">
                        {job.description}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] text-gray-500 dark:text-gray-400 mt-1">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-2.5 h-2.5" />
                        {jobGarage}
                      </span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-2.5 h-2.5" />
                        {job.date}
                      </span>
                      <span>·</span>
                      <span>{job.charge > 0 ? formatCurrency(job.charge) : 'Internal work'}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        job.status === 'Open'
                          ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200/60'
                          : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200/60'
                      }`}
                    >
                      {job.status}
                    </span>

                    <button
                      onClick={() => onViewJobDetail?.(job)}
                      className="px-2.5 py-1 rounded-lg text-xs font-bold text-gray-600 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700 transition cursor-pointer"
                    >
                      Details
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Exact empty-state message from IMAGE 2: "No garage jobs yet." */
          <div className="py-12 text-center flex flex-col items-center justify-center gap-1.5">
            <div className="w-9 h-9 rounded-full bg-[var(--theme-primary-soft)] dark:bg-zinc-800 flex items-center justify-center mb-1">
              <Wrench className="w-4 h-4 text-[var(--theme-primary)]" />
            </div>
            <p className="text-xs font-bold text-gray-600 dark:text-gray-400">
              No garage jobs yet.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
