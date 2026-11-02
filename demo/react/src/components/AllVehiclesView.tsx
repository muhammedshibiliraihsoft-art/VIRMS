import React, { useState, useMemo, useEffect } from 'react';
import {
  Car,
  Search,
  Plus,
  ExternalLink,
  Layers,
  MapPin,
  User,
  TrendingUp,
  Wrench,
  DollarSign,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react';
import { Vehicle, Garage, VehicleStatus } from '../types';
import { useCanPresentBusinessWriteActions } from '../auth/RolePresentationContext';
import { getFormDataSourceStatus } from '../data/navigationRegistry';
import { DemoBadge } from './shared/DemoBadge';

export type VehiclePageMode = 'all' | 'stock-investor' | 'customer';

export interface AllVehiclesViewProps {
  mode?: VehiclePageMode;
  vehicles: Vehicle[];
  garages: Garage[];
  selectedGarage: string;
  onRegisterVehicle: () => void;
  onViewVehicleDetail?: (vehicle: Vehicle) => void;
  onSelectRoute?: (routeKey: string) => void;
}

export const AllVehiclesView: React.FC<AllVehiclesViewProps> = ({
  mode = 'all',
  vehicles,
  garages,
  selectedGarage,
  onRegisterVehicle,
  onViewVehicleDetail,
  onSelectRoute,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const [searchQuery, setSearchQuery] = useState('');
  // Internal filter state defaults based on mode
  const [typeFilter, setTypeFilter] = useState<'All' | 'Stock / Investor' | 'Customer'>(() => {
    if (mode === 'stock-investor') return 'Stock / Investor';
    if (mode === 'customer') return 'Customer';
    return 'All';
  });
  const [statusFilter, setStatusFilter] = useState<string>('All');

  // Sync type filter when incoming mode changes
  useEffect(() => {
    if (mode === 'stock-investor') {
      setTypeFilter('Stock / Investor');
    } else if (mode === 'customer') {
      setTypeFilter('Customer');
    } else {
      setTypeFilter('All');
    }
    setStatusFilter('All');
  }, [mode]);

  // Garage-filtered dataset (Respecting global garage filter from shared AppShell)
  const garageFilteredVehicles = useMemo(() => {
    return vehicles.filter(
      (v) => selectedGarage === 'all' || v.garageId === selectedGarage
    );
  }, [vehicles, selectedGarage]);

  // Derived filter counts and financial summaries
  const stats = useMemo(() => {
    const total = garageFilteredVehicles.length;
    const stockVehicles = garageFilteredVehicles.filter((v) => v.type === 'Stock / Investor');
    const customerVehicles = garageFilteredVehicles.filter((v) => v.type === 'Customer');

    const stockTotalCost = stockVehicles.reduce(
      (acc, v) => acc + (v.totalCost ?? v.purchase ?? 0),
      0
    );

    const inWork = garageFilteredVehicles.filter((v) => v.status === 'In work').length;
    const sold = garageFilteredVehicles.filter((v) => v.status === 'Sold').length;
    const purchased = garageFilteredVehicles.filter((v) => v.status === 'Purchased').length;
    const customerJobs = customerVehicles.length;

    const stockInWork = stockVehicles.filter((v) => v.status === 'In work').length;
    const stockPurchased = stockVehicles.filter((v) => v.status === 'Purchased').length;
    const stockSold = stockVehicles.filter((v) => v.status === 'Sold').length;

    return {
      total,
      stockCount: stockVehicles.length,
      customerCount: customerVehicles.length,
      stockTotalCost,
      inWork,
      sold,
      purchased,
      customerJobs,
      stockInWork,
      stockPurchased,
      stockSold,
    };
  }, [garageFilteredVehicles]);

  // Search & Filtered vehicles list
  const displayedVehicles = useMemo(() => {
    return garageFilteredVehicles.filter((veh) => {
      // Type filter
      if (typeFilter !== 'All' && veh.type !== typeFilter) return false;

      // Status filter
      if (statusFilter !== 'All') {
        if (statusFilter === 'Customer Vehicles' && veh.type !== 'Customer') return false;
        if (statusFilter !== 'Customer Vehicles' && veh.status !== statusFilter) return false;
      }

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesNumber = veh.number.toLowerCase().includes(q);
        const matchesModel = veh.model.toLowerCase().includes(q);
        const matchesPerson = veh.person.toLowerCase().includes(q);
        return matchesNumber || matchesModel || matchesPerson;
      }

      return true;
    });
  }, [garageFilteredVehicles, typeFilter, statusFilter, searchQuery]);

  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    return '₹' + val.toLocaleString('en-IN');
  };

  const getGarageName = (garageId: string) => {
    const g = garages.find((item) => item.id === garageId);
    return g ? g.name : 'Central Garage';
  };

  const getStatusBadge = (status: VehicleStatus) => {
    switch (status) {
      case 'In work':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[8px] sm:text-[9px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200/60 shrink-0">
            <span className="w-1 h-1 rounded-full bg-amber-500 animate-pulse" />
            In work
          </span>
        );
      case 'Sold':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[8px] sm:text-[9px] font-bold bg-gray-100 text-gray-700 dark:bg-zinc-800 dark:text-gray-300 border border-gray-200/70 dark:border-zinc-700 shrink-0">
            Sold
          </span>
        );
      case 'Purchased':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[8px] sm:text-[9px] font-bold bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200/60 shrink-0">
            Purchased
          </span>
        );
      case 'Customer Vehicle':
      case 'In service':
      case 'Completed':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[8px] sm:text-[9px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200/60 shrink-0">
            {status}
          </span>
        );
    }
  };

  // Header Titles based on mode
  const pageMeta = useMemo(() => {
    switch (mode) {
      case 'stock-investor':
        return {
          title: 'Stock / Investor Vehicles',
          subtitle: 'Vehicles acquired with investor capital for inventory and resale.',
          badge: 'Stock Register',
        };
      case 'customer':
        return {
          title: 'Customer Vehicles',
          subtitle: 'Vehicles registered for customer service, repairs, and garage jobs.',
          badge: 'Customer Intake',
        };
      case 'all':
      default:
        return {
          title: 'All Vehicles',
          subtitle: 'Shared synthetic data across vehicles, jobs, inventory and accounting.',
          badge: 'Consolidated Register',
        };
    }
  }, [mode]);

  return (
    <div className="flex flex-col gap-3.5 sm:gap-4 animate-in fade-in duration-150">
      {/* 1. Header & Top Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-0.5 pb-0.5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight">
              {pageMeta.title}
            </h1>
            <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] text-[10px] font-bold border border-[var(--theme-primary-border)]">
              {pageMeta.badge}
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium">
            {pageMeta.subtitle}
          </p>
        </div>

        {/* Right Action Bar: Filters + Search + Register Vehicle Button */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Category Filter Pills */}
          <div className="flex items-center p-0.5 bg-gray-100/80 dark:bg-zinc-800/80 rounded-full border border-gray-200/60 dark:border-zinc-700 text-xs font-semibold">
            {(['All', 'Stock / Investor', 'Customer'] as const).map((type) => {
              const isActive = typeFilter === type;
              return (
                <button
                  key={type}
                  onClick={() => {
                    setTypeFilter(type);
                    setStatusFilter('All');
                    if (onSelectRoute) {
                      if (type === 'Stock / Investor') onSelectRoute('Stock / Investor');
                      else if (type === 'Customer') onSelectRoute('Customer Vehicles');
                      else onSelectRoute('All Vehicles');
                    }
                  }}
                  className={`px-2.5 sm:px-3 py-1 rounded-full text-[10px] sm:text-[11px] font-bold transition-all cursor-pointer ${
                    isActive
                      ? 'bg-black text-white shadow-xs dark:bg-white dark:text-black'
                      : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'
                  }`}
                >
                  {type === 'Stock / Investor' ? 'Stock' : type === 'Customer' ? 'Customer' : 'All'}
                </button>
              );
            })}
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search registration, model..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1 rounded-full bg-white dark:bg-zinc-800/80 border border-gray-200/80 dark:border-zinc-700 text-[11px] font-medium text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary-border)] focus:border-[var(--theme-primary)] w-36 sm:w-44 shadow-2xs transition"
            />
          </div>

          {/* + Register Vehicle */}
          {canPresentWriteActions && <button
            onClick={onRegisterVehicle}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#18181b] hover:bg-black text-white text-xs font-bold shadow-xs transition-all cursor-pointer active:scale-95"
          >
            <Plus className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
            <span>Register Vehicle</span>
            {getFormDataSourceStatus('vehicle') === 'demo' && <DemoBadge size="compact" />}
          </button>}
        </div>
      </div>

      {/* 2. Main Two-Zone Layout: Vehicle Cards (Left) + Vehicle Summary Panel (Right) */}
      <div className="flex flex-col lg:flex-row items-start gap-3.5 sm:gap-4">
        {/* Left Area: Responsive Compact Vehicle Card Grid (~50% visual size, 4-5 per row on desktop) */}
        <div className="flex-1 min-w-0 w-full">
          {displayedVehicles.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-2 sm:gap-2.5">
              {displayedVehicles.map((veh) => {
                const isCustomer = veh.type === 'Customer';
                return (
                  <div
                    key={veh.id}
                    className="bg-[var(--theme-card-bg)] dark:bg-zinc-800/70 border border-[var(--theme-card-border)] dark:border-zinc-700/60 rounded-[18px] p-2.5 sm:p-3 flex flex-col justify-between shadow-2xs hover:shadow-sm hover:border-[var(--theme-primary-border)] dark:hover:border-zinc-600 transition-all duration-200 group"
                  >
                    {/* Compact Top Visual Area (~50% height: h-16 sm:h-20) */}
                    <div className="h-16 sm:h-20 rounded-xl bg-gradient-to-br from-[var(--theme-primary-soft)] via-transparent to-[var(--theme-primary-subtle)] dark:from-zinc-800 dark:to-zinc-800/60 border border-[var(--theme-primary-border)] dark:border-zinc-700/50 p-2 flex flex-col justify-between relative overflow-hidden mb-2">
                      {/* Top Row: Type Pill Badge + Garage Location */}
                      <div className="flex items-center justify-between z-10 gap-1">
                        <span className="px-1.5 py-0.5 rounded-full bg-black/85 text-white dark:bg-white dark:text-black text-[8px] sm:text-[9px] font-bold shadow-2xs shrink-0 whitespace-nowrap">
                          {veh.type === 'Stock / Investor' ? 'Stock' : veh.type}
                        </span>

                        <div className="flex items-center gap-0.5 text-[8px] sm:text-[9px] font-semibold text-gray-600 dark:text-gray-400 bg-white/80 dark:bg-zinc-900/70 backdrop-blur-xs px-1.5 py-0.5 rounded-full border border-gray-200/50 dark:border-zinc-700/60 truncate max-w-[100px]">
                          <MapPin className="w-2 h-2 text-gray-400 shrink-0" />
                          <span className="truncate">{getGarageName(veh.garageId)}</span>
                        </div>
                      </div>

                      {/* Center Decorative Visual Area (Compact Monogram Symbol) */}
                      <div className="my-auto flex items-center justify-center z-10">
                        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-white/85 dark:bg-zinc-800/85 border border-white/60 dark:border-zinc-700 shadow-2xs flex items-center justify-center text-gray-800 dark:text-gray-200 group-hover:scale-105 transition-transform duration-200">
                          <Car className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[var(--theme-primary)]" />
                        </div>
                      </div>

                      {/* Bottom Visual Subtle Shimmer Accent */}
                      <div className="flex items-center justify-between z-10 text-[8px] font-semibold text-gray-400 dark:text-gray-500">
                        <span className="uppercase tracking-wider">VIRMS</span>
                        <span>#{veh.id}</span>
                      </div>

                      {/* Ambient background glow */}
                      <div className="absolute -right-3 -bottom-3 w-16 h-16 rounded-full bg-[var(--theme-primary-soft)] blur-lg pointer-events-none" />
                    </div>

                    {/* Card Body: Identification & Owner */}
                    <div>
                      <div className="flex items-baseline justify-between gap-1 mb-0.5">
                        <h2 className="text-xs sm:text-sm font-extrabold text-gray-950 dark:text-white tracking-tight truncate">
                          {veh.number}
                        </h2>
                        {getStatusBadge(veh.status)}
                      </div>

                      <p className="text-[11px] font-semibold text-gray-700 dark:text-gray-300 truncate mb-1.5">
                        {veh.model}
                      </p>

                      <div className="flex items-center gap-1 text-[10px] text-gray-500 dark:text-gray-400 py-0.5 border-t border-gray-100 dark:border-zinc-750">
                        <User className="w-2.5 h-2.5 text-gray-400 shrink-0" />
                        <span className="truncate">{veh.person}</span>
                        <span className="text-[9px] opacity-60">·</span>
                        <span className="text-[9px] opacity-75 shrink-0">
                          {isCustomer ? 'Customer' : 'Investor'}
                        </span>
                      </div>
                    </div>

                    {/* Card Footer: Financial Total Cost & Action Link */}
                    <div className="pt-1.5 mt-1 border-t border-gray-100 dark:border-zinc-750 flex items-center justify-between">
                      <div>
                        <div className="text-[8px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                          Total Cost
                        </div>
                        <div className="text-xs sm:text-sm font-extrabold text-gray-950 dark:text-white">
                          {formatCurrency(veh.totalCost ?? veh.purchase)}
                        </div>
                      </div>

                      <button
                        onClick={() => onViewVehicleDetail?.(veh)}
                        title="View details"
                        className="flex items-center gap-0.5 text-[10px] font-bold text-gray-600 hover:text-black dark:text-gray-400 dark:hover:text-white px-1.5 py-0.5 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 transition cursor-pointer"
                      >
                        <span>Details</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Friendly Empty State */
            <div className="bg-[var(--theme-card-bg)] dark:bg-zinc-800/70 border border-[var(--theme-card-border)] dark:border-zinc-700/60 rounded-[18px] p-8 text-center flex flex-col items-center justify-center gap-2">
              <div className="w-10 h-10 rounded-full bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] flex items-center justify-center">
                <Car className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-gray-900 dark:text-white">No vehicles found</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 max-w-sm">
                No vehicles matched your search or selected filter. Try adjusting your query or filter criteria.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setTypeFilter(mode === 'stock-investor' ? 'Stock / Investor' : mode === 'customer' ? 'Customer' : 'All');
                  setStatusFilter('All');
                }}
                className="mt-2 text-xs font-bold text-[var(--theme-primary)] hover:underline cursor-pointer"
              >
                Reset filters
              </button>
            </div>
          )}
        </div>

        {/* Right Area: Vehicle Groups / Summary Panel (Compact & Mode-Aware) */}
        <aside
          aria-label="Vehicle Groups Summary"
          className="w-full lg:w-64 xl:w-72 shrink-0 bg-[var(--theme-card-bg)] dark:bg-zinc-800/70 border border-[var(--theme-card-border)] dark:border-zinc-700/60 rounded-[20px] p-3.5 sm:p-4 flex flex-col gap-3.5 shadow-2xs"
        >
          {/* Panel Header */}
          <div className="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-zinc-750">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[var(--theme-primary)]" />
              <h2 className="text-xs sm:text-sm font-bold text-gray-950 dark:text-white">
                {mode === 'stock-investor'
                  ? 'Stock Overview'
                  : mode === 'customer'
                  ? 'Customer Service'
                  : 'Vehicle Groups'}
              </h2>
            </div>
            <span className="w-5 h-5 rounded-full bg-gray-100 dark:bg-zinc-800 text-[10px] font-bold text-gray-600 dark:text-gray-300 flex items-center justify-center">
              {displayedVehicles.length}
            </span>
          </div>

          {/* Mode-Specific Highlight Card */}
          {mode === 'stock-investor' ? (
            <div className="bg-[var(--theme-primary-soft)] border border-[var(--theme-primary-border)] rounded-xl p-2.5 flex flex-col gap-1">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-[var(--theme-primary)]">
                <DollarSign className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
                <span>Total Capital Invested</span>
              </div>
              <div className="text-base sm:text-lg font-black text-gray-950 dark:text-white">
                {formatCurrency(stats.stockTotalCost)}
              </div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400">
                Across {stats.stockCount} stock/inventory vehicles
              </div>
            </div>
          ) : mode === 'customer' ? (
            <div className="bg-emerald-50/70 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-800/40 rounded-xl p-2.5 flex flex-col gap-1">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-800 dark:text-emerald-300">
                <Wrench className="w-3.5 h-3.5 text-emerald-600" />
                <span>Active Service Intake</span>
              </div>
              <div className="text-base sm:text-lg font-black text-gray-950 dark:text-white">
                {stats.customerCount} Units
              </div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400">
                Under customer repair & maintenance
              </div>
            </div>
          ) : null}

          {/* Ownership Breakdown Links */}
          <div className="flex flex-col gap-1.5">
            <div className="text-[9px] font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">
              By Ownership
            </div>

            {/* All Vehicles */}
            <button
              onClick={() => {
                setTypeFilter('All');
                setStatusFilter('All');
                if (onSelectRoute) onSelectRoute('All Vehicles');
              }}
              className={`w-full flex flex-col gap-1 p-2 rounded-xl text-left transition cursor-pointer ${
                typeFilter === 'All' && statusFilter === 'All'
                  ? 'bg-black text-white dark:bg-white dark:text-black shadow-xs'
                  : 'hover:bg-gray-100/70 dark:hover:bg-zinc-800/60 text-gray-800 dark:text-gray-200'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-semibold">
                <span>All Vehicles</span>
                <span className="text-[10px] opacity-80">{stats.total} items</span>
              </div>
              <div className="w-full h-1 rounded-full bg-gray-200 dark:bg-zinc-700 overflow-hidden">
                <div className="h-full bg-[var(--theme-primary)] rounded-full" style={{ width: '100%' }} />
              </div>
            </button>

            {/* Stock / Investor */}
            <button
              onClick={() => {
                setTypeFilter('Stock / Investor');
                setStatusFilter('All');
                if (onSelectRoute) onSelectRoute('Stock / Investor');
              }}
              className={`w-full flex flex-col gap-1 p-2 rounded-xl text-left transition cursor-pointer ${
                typeFilter === 'Stock / Investor' && statusFilter === 'All'
                  ? 'bg-black text-white dark:bg-white dark:text-black shadow-xs'
                  : 'hover:bg-gray-100/70 dark:hover:bg-zinc-800/60 text-gray-800 dark:text-gray-200'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-semibold">
                <span>Stock / Investor</span>
                <span className="text-[10px] opacity-80">{stats.stockCount} items</span>
              </div>
              <div className="w-full h-1 rounded-full bg-gray-200 dark:bg-zinc-700 overflow-hidden">
                <div
                  className="h-full bg-[var(--theme-primary)] rounded-full"
                  style={{
                    width: `${stats.total > 0 ? (stats.stockCount / stats.total) * 100 : 0}%`,
                  }}
                />
              </div>
            </button>

            {/* Customer Vehicles */}
            <button
              onClick={() => {
                setTypeFilter('Customer');
                setStatusFilter('All');
                if (onSelectRoute) onSelectRoute('Customer Vehicles');
              }}
              className={`w-full flex flex-col gap-1 p-2 rounded-xl text-left transition cursor-pointer ${
                typeFilter === 'Customer' && statusFilter === 'All'
                  ? 'bg-black text-white dark:bg-white dark:text-black shadow-xs'
                  : 'hover:bg-gray-100/70 dark:hover:bg-zinc-800/60 text-gray-800 dark:text-gray-200'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-semibold">
                <span>Customer Vehicles</span>
                <span className="text-[10px] opacity-80">{stats.customerCount} items</span>
              </div>
              <div className="w-full h-1 rounded-full bg-gray-200 dark:bg-zinc-700 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{
                    width: `${stats.total > 0 ? (stats.customerCount / stats.total) * 100 : 0}%`,
                  }}
                />
              </div>
            </button>
          </div>

          {/* Lifecycle Status Breakdown */}
          <div className="flex flex-col gap-1.5 pt-2 border-t border-gray-100 dark:border-zinc-750">
            <div className="text-[9px] font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">
              By Lifecycle Status
            </div>

            {/* In work */}
            <button
              onClick={() => setStatusFilter((prev) => (prev === 'In work' ? 'All' : 'In work'))}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-[11px] font-semibold transition cursor-pointer ${
                statusFilter === 'In work'
                  ? 'bg-amber-50 text-amber-900 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-200'
                  : 'hover:bg-gray-100/70 dark:hover:bg-zinc-800/60 text-gray-700 dark:text-gray-300'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span>In work</span>
              </div>
              <span className="text-[10px] font-bold">
                {mode === 'stock-investor' ? stats.stockInWork : stats.inWork}
              </span>
            </button>

            {/* Purchased */}
            <button
              onClick={() => setStatusFilter((prev) => (prev === 'Purchased' ? 'All' : 'Purchased'))}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-[11px] font-semibold transition cursor-pointer ${
                statusFilter === 'Purchased'
                  ? 'bg-blue-50 text-blue-900 border border-blue-200 dark:bg-blue-950/40 dark:text-blue-200'
                  : 'hover:bg-gray-100/70 dark:hover:bg-zinc-800/60 text-gray-700 dark:text-gray-300'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                <span>Purchased</span>
              </div>
              <span className="text-[10px] font-bold">
                {mode === 'stock-investor' ? stats.stockPurchased : stats.purchased}
              </span>
            </button>

            {/* Sold */}
            <button
              onClick={() => setStatusFilter((prev) => (prev === 'Sold' ? 'All' : 'Sold'))}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-[11px] font-semibold transition cursor-pointer ${
                statusFilter === 'Sold'
                  ? 'bg-gray-200 text-gray-900 border border-gray-300 dark:bg-zinc-800 dark:text-white'
                  : 'hover:bg-gray-100/70 dark:hover:bg-zinc-800/60 text-gray-700 dark:text-gray-300'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                <span>Sold</span>
              </div>
              <span className="text-[10px] font-bold">
                {mode === 'stock-investor' ? stats.stockSold : stats.sold}
              </span>
            </button>

            {/* Customer Service */}
            {mode !== 'stock-investor' && (
              <button
                onClick={() => {
                  setTypeFilter('Customer');
                  setStatusFilter('All');
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-[11px] font-semibold transition cursor-pointer ${
                  typeFilter === 'Customer'
                    ? 'bg-emerald-50 text-emerald-900 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-200'
                    : 'hover:bg-gray-100/70 dark:hover:bg-zinc-800/60 text-gray-700 dark:text-gray-300'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Customer Service</span>
                </div>
                <span className="text-[10px] font-bold">{stats.customerCount}</span>
              </button>
            )}
          </div>

          {/* Bottom Counter */}
          <div className="pt-2.5 border-t border-gray-100 dark:border-zinc-750 text-[11px] font-bold text-gray-900 dark:text-white flex items-baseline gap-1.5">
            <span className="text-lg font-extrabold text-[var(--theme-primary)]">
              {displayedVehicles.length}
            </span>
            <span className="text-gray-500 dark:text-gray-400 font-medium">
              vehicles listed in view
            </span>
          </div>
        </aside>
      </div>
    </div>
  );
};

export const VehiclesPageView = AllVehiclesView;
