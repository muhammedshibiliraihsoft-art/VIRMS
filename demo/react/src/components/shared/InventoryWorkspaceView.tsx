import React, { useState } from 'react';
import {
  Package,
  Plus,
  Search,
  Building2,
  ArrowRight,
  TrendingUp,
  Tag,
  Layers,
} from 'lucide-react';
import { Data, Garage } from '../../types';
import { remaining, margin, issueGarage } from '../../utils/selectors';
import { FormModalType } from './SharedFormModal';
import { useCanPresentBusinessWriteActions } from '../../auth/RolePresentationContext';
import { getFormDataSourceStatus } from '../../data/navigationRegistry';
import { DemoBadge } from './DemoBadge';

interface InventoryWorkspaceViewProps {
  initialTab?: 'items-purchases' | 'stock-issues' | 'stock-reports';
  data: Data;
  garages: Garage[];
  selectedGarage: string;
  onSelectGarage: (garageId: string) => void;
  onOpenFormModal: (type: FormModalType, initialContext?: Record<string, any>) => void;
}

export const InventoryWorkspaceView: React.FC<InventoryWorkspaceViewProps> = ({
  initialTab = 'items-purchases',
  data,
  garages,
  selectedGarage,
  onSelectGarage,
  onOpenFormModal,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const [activeSubTab, setActiveSubTab] = useState<'items-purchases' | 'stock-issues' | 'stock-reports'>(initialTab);
  const [searchQuery, setSearchQuery] = useState('');
  const formatINR = (val: number) => '₹' + Math.round(val).toLocaleString('en-IN');

  const inScope = (gId?: string) => selectedGarage === 'all' || !gId || gId === selectedGarage;

  // Inventory Totals
  const totalStockValue = (data.batches || [])
    .filter((b) => inScope(b.garageId))
    .reduce((s, b) => s + remaining(data, b) * b.cost, 0);

  const totalMargin = margin(data);
  const totalBatches = (data.batches || []).filter((b) => inScope(b.garageId)).length;

  return (
    <div className="space-y-4 sm:space-y-5 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-[#f2ebe5] dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">
            INVENTORY MANAGEMENT
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            Workshop Parts & Stock Workspace
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium">
            Manage part catalog, batch procurement, and vehicle issue allocations.
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

          {/* Action Buttons */}
          {canPresentWriteActions && <button
            onClick={() => onOpenFormModal('purchase')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#18181b] hover:bg-black text-white text-xs font-bold shadow-xs transition cursor-pointer active:scale-95"
          >
            <Plus className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
            <span>Purchase Batch</span>
            {getFormDataSourceStatus('purchase') === 'demo' && <DemoBadge size="compact" />}
          </button>}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="dashboard-card-orange text-white rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px] shadow-xs">
          <span className="text-[11px] font-medium text-white/90 leading-none">
            Remaining Stock Valuation
          </span>
          <span className="text-2xl sm:text-[27px] font-bold tracking-tight my-auto text-white">
            {formatINR(totalStockValue)}
          </span>
        </div>

        <div className="dashboard-card-solid rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400 leading-none">
            Realized Issue Margin
          </span>
          <span className="text-2xl sm:text-[27px] font-bold tracking-tight my-auto text-gray-950 dark:text-white">
            {formatINR(totalMargin)}
          </span>
        </div>

        <div className="dashboard-card-solid rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px]">
          <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400 leading-none">
            Active Warehouse Batches
          </span>
          <span className="text-2xl sm:text-[27px] font-bold tracking-tight my-auto text-gray-950 dark:text-white">
            {totalBatches}
          </span>
        </div>
      </div>

      {/* Sub Tabs */}
      <div className="flex items-center gap-2 border-b border-[#f0e7df] dark:border-zinc-800 pb-2">
        {[
          { id: 'items-purchases', label: 'Items & Purchases' },
          { id: 'stock-issues', label: 'Stock Issues' },
          { id: 'stock-reports', label: 'Stock Reports & Valuation' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id as any)}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              activeSubTab === tab.id
                ? 'bg-[#18181b] text-white shadow-2xs'
                : 'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Items & Purchases */}
      {activeSubTab === 'items-purchases' && (
        <div className="dashboard-card-solid rounded-[24px] overflow-hidden">
          <div className="p-4 px-5 border-b border-[#f0e7df] dark:border-zinc-800 flex items-center justify-between gap-3">
            <h3 className="text-sm font-bold text-gray-950 dark:text-white">
              Procured Batches & Catalog
            </h3>
            {canPresentWriteActions && <button
              onClick={() => onOpenFormModal('purchase')}
              className="inline-flex items-center gap-1 text-xs font-bold text-[var(--theme-primary)] hover:underline"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Batch</span>
              {getFormDataSourceStatus('purchase') === 'demo' && <DemoBadge size="compact" />}
            </button>}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#f0e7df] dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/30">
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Item</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Category</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Garage</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Initial Qty</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Remaining</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Unit Cost</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f5ede5] dark:divide-zinc-800/60">
                {(data.batches || [])
                  .filter((b) => inScope(b.garageId))
                  .map((b) => {
                    const it = (data.items || []).find((item) => item.id === b.itemId);
                    const g = (data.garages || []).find((x) => x.id === b.garageId);
                    const rem = remaining(data, b);
                    return (
                      <tr key={b.id} className="hover:bg-gray-50/70 dark:hover:bg-zinc-800/40">
                        <td className="py-3 px-4 font-bold text-gray-900 dark:text-gray-100">{it?.name ?? 'Part'}</td>
                        <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{it?.category ?? 'General'}</td>
                        <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{g?.name ?? 'Central'}</td>
                        <td className="py-3 px-4 text-right font-mono font-medium">{b.quantity}</td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-gray-900 dark:text-white">{rem}</td>
                        <td className="py-3 px-4 text-right font-mono font-medium">{formatINR(b.cost)}</td>
                        <td className="py-3 px-4 text-right text-gray-500">{b.date}</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Stock Issues */}
      {activeSubTab === 'stock-issues' && (
        <div className="dashboard-card-solid rounded-[24px] overflow-hidden">
          <div className="p-4 px-5 border-b border-[#f0e7df] dark:border-zinc-800 flex items-center justify-between gap-3">
            <h3 className="text-sm font-bold text-gray-950 dark:text-white">
              Dispensed Stock to Jobs & Vehicles
            </h3>
            {canPresentWriteActions && <button
              onClick={() => onOpenFormModal('issue')}
              className="inline-flex items-center gap-1 text-xs font-bold text-[var(--theme-primary)] hover:underline"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Issue Stock</span>
              {getFormDataSourceStatus('issue') === 'demo' && <DemoBadge size="compact" />}
            </button>}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#f0e7df] dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/30">
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Date</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Item</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Vehicle / Job</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Qty</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Price</th>
                  <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Total Billed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f5ede5] dark:divide-zinc-800/60">
                {(data.issues || []).map((i) => {
                  const b = (data.batches || []).find((bat) => bat.id === i.batchId);
                  const it = (data.items || []).find((item) => item.id === b?.itemId);
                  const v = (data.vehicles || []).find((veh) => veh.id === i.vehicleId);
                  const j = (data.jobs || []).find((job) => job.id === i.jobId);
                  return (
                    <tr key={i.id} className="hover:bg-gray-50/70 dark:hover:bg-zinc-800/40">
                      <td className="py-3 px-4 text-gray-500">{i.date}</td>
                      <td className="py-3 px-4 font-bold text-gray-900 dark:text-gray-100">{it?.name ?? 'Part'}</td>
                      <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                        {v ? `${v.model} (${v.number})` : ''} {j ? `· ${j.number}` : ''}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-medium">{i.quantity}</td>
                      <td className="py-3 px-4 text-right font-mono font-medium">{formatINR(i.price)}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-gray-900 dark:text-white">
                        {formatINR(i.quantity * i.price)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Stock Reports */}
      {activeSubTab === 'stock-reports' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="dashboard-card-solid rounded-[24px] p-5 space-y-3">
            <h3 className="text-sm font-bold text-gray-950 dark:text-white">
              Remaining Asset Valuation by Item
            </h3>
            <div className="space-y-2">
              {(data.items || []).map((item) => {
                const itemBatches = (data.batches || []).filter(
                  (b) => b.itemId === item.id && inScope(b.garageId)
                );
                const remQty = itemBatches.reduce((s, b) => s + remaining(data, b), 0);
                const val = itemBatches.reduce((s, b) => s + remaining(data, b) * b.cost, 0);
                return (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-gray-50/60 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800"
                  >
                    <div>
                      <span className="text-xs font-bold text-gray-900 dark:text-white block">
                        {item.name}
                      </span>
                      <span className="text-[11px] text-gray-500 dark:text-gray-400">
                        {item.category} · {remQty} units remaining
                      </span>
                    </div>
                    <span className="text-xs font-bold font-mono text-gray-950 dark:text-white">
                      {formatINR(val)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="dashboard-card-solid rounded-[24px] p-5 space-y-3">
            <h3 className="text-sm font-bold text-gray-950 dark:text-white">
              Markup & Profit Margin by Item
            </h3>
            <div className="space-y-2">
              {(data.items || []).map((item) => {
                const issues = (data.issues || []).filter((i) => {
                  const b = (data.batches || []).find((bat) => bat.id === i.batchId);
                  return b?.itemId === item.id && inScope(issueGarage(data, i));
                });
                const totalRev = issues.reduce((s, i) => s + i.quantity * i.price, 0);
                const totalCost = issues.reduce((s, i) => {
                  const b = (data.batches || []).find((bat) => bat.id === i.batchId);
                  return s + i.quantity * (b?.cost ?? 0);
                }, 0);
                const grossMargin = totalRev - totalCost;
                return (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-gray-50/60 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800"
                  >
                    <div>
                      <span className="text-xs font-bold text-gray-900 dark:text-white block">
                        {item.name}
                      </span>
                      <span className="text-[11px] text-gray-500 dark:text-gray-400">
                        Revenue: {formatINR(totalRev)} · Cost: {formatINR(totalCost)}
                      </span>
                    </div>
                    <span className="text-xs font-bold font-mono text-emerald-600 dark:text-emerald-400">
                      +{formatINR(grossMargin)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
