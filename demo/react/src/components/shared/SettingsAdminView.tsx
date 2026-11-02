import React, { useState, useEffect } from 'react';
import {
  Building2,
  Database,
  Plus,
  RefreshCw,
  Download,
  Upload,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Palette,
  Check,
} from 'lucide-react';
import { Data, Garage } from '../../types';
import { initialData } from '../../data/mockData';
import { FormModalType } from './SharedFormModal';
import { THEME_REGISTRY, DEFAULT_THEME_ID } from '../../theme/themeRegistry';

export type SettingsTabType = 'garages-branches' | 'theme-appearance' | 'demo-data';

interface SettingsAdminViewProps {
  initialTab?: SettingsTabType;
  data: Data;
  currentThemePalette: string;
  onSelectThemePalette: (themeId: string) => void;
  onUpdateData: (updater: (prev: Data) => Data) => void;
  onOpenFormModal: (type: FormModalType, initialContext?: Record<string, any>) => void;
  onSuccessMessage: (msg: string) => void;
  showNonThemeTabs?: boolean;
}

export const SettingsAdminView: React.FC<SettingsAdminViewProps> = ({
  initialTab = 'garages-branches',
  data,
  currentThemePalette,
  onSelectThemePalette,
  onUpdateData,
  onOpenFormModal,
  onSuccessMessage,
  showNonThemeTabs = false,
}) => {
  const [activeTab, setActiveTab] = useState<SettingsTabType>(initialTab);
  const [jsonInput, setJsonInput] = useState('');
  const [showImportArea, setShowImportArea] = useState(false);
  const visibleTab = showNonThemeTabs ? activeTab : 'theme-appearance';

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  const handleExportJson = () => {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `virms-snapshot-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    onSuccessMessage('VIRMS snapshot downloaded successfully.');
  };

  const handleResetSeed = () => {
    if (window.confirm('Reset all demo data back to clean canonical seed? Any uncommitted changes will be replaced.')) {
      onUpdateData(() => initialData);
      onSuccessMessage('Demo session reset to initial seed state.');
    }
  };

  const handleImportJson = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      if (!parsed.garages || !parsed.vehicles || !parsed.jobs) {
        throw new Error('Invalid VIRMS snapshot format. Missing core entities.');
      }
      onUpdateData(() => parsed);
      setShowImportArea(false);
      setJsonInput('');
      onSuccessMessage('Snapshot imported successfully.');
    } catch (err: any) {
      alert('Import failed: ' + err.message);
    }
  };

  const handleToggleGarageStatus = (garageId: string) => {
    onUpdateData((prev) => ({
      ...prev,
      garages: prev.garages.map((g) =>
        g.id === garageId ? { ...g, active: !g.active } : g
      ),
    }));
    onSuccessMessage('Garage status updated.');
  };

  const themesList = Object.values(THEME_REGISTRY);

  return (
    <div className="space-y-4 sm:space-y-5 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-[#f2ebe5] dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">
            {showNonThemeTabs ? 'SYSTEM ADMINISTRATION' : 'PREFERENCES'}
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            {showNonThemeTabs ? 'Settings & Workspace Governance' : 'Appearance & Theme'}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium">
            {showNonThemeTabs
              ? 'Manage physical workshop locations, brand themes, and session demo snapshots.'
              : 'Customize the appearance of this prototype workspace.'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 flex-wrap">
          {showNonThemeTabs && <button
            onClick={() => setActiveTab('garages-branches')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              activeTab === 'garages-branches'
                ? 'bg-[#18181b] text-white shadow-2xs'
                : 'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50'
            }`}
          >
            Garages / Branches
          </button>}
          <button
            onClick={() => setActiveTab('theme-appearance')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              visibleTab === 'theme-appearance'
                ? 'bg-[#18181b] text-white shadow-2xs'
                : 'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50'
            }`}
          >
            <Palette className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
            <span>Appearance & Theme</span>
          </button>
          {showNonThemeTabs && <button
            onClick={() => setActiveTab('demo-data')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              activeTab === 'demo-data'
                ? 'bg-[#18181b] text-white shadow-2xs'
                : 'bg-white dark:bg-zinc-800 text-gray-600 dark:text-gray-300 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50'
            }`}
          >
            Demo Data & Seed
          </button>}
        </div>
      </div>

      {/* Tab 1: Appearance & Theme (CONTROLLED INSIDE SETTINGS ONLY) */}
      {visibleTab === 'theme-appearance' && (
        <div className="space-y-4">
          <div className="dashboard-card-solid rounded-[24px] p-6 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-base font-extrabold text-gray-950 dark:text-white">
                  Brand Theme & Visual Palette
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-300 mt-1 leading-relaxed max-w-2xl">
                  Select the central brand palette for the VIRMS interface. The selected theme consistently controls primary buttons, navigation indicators, active tabs, focus states, and the background wash while strictly preserving semantic status indicators (In work, In service, Completed).
                </p>
              </div>
              <div className="px-3 py-1.5 rounded-full bg-gray-50 dark:bg-zinc-800 border border-[#e2d8ce] dark:border-zinc-700 text-xs font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2 shrink-0">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--theme-primary)]" />
                <span>Active: {THEME_REGISTRY[currentThemePalette]?.name || 'Orange'}</span>
              </div>
            </div>

            {/* Theme Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-2">
              {themesList.map((t) => {
                const isSelected = t.id === currentThemePalette;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => onSelectThemePalette(t.id)}
                    className={`text-left p-4 rounded-[20px] transition-all cursor-pointer relative border flex flex-col justify-between min-h-[148px] ${
                      isSelected
                        ? 'bg-white dark:bg-zinc-800/90 border-[var(--theme-primary)] shadow-md ring-2 ring-[var(--theme-primary)]/20'
                        : 'bg-white/80 dark:bg-zinc-800/40 border-[#ebe2d8] dark:border-zinc-700/80 hover:border-gray-400 dark:hover:border-zinc-600'
                    }`}
                  >
                    <div>
                      {/* Top: Theme Name & Badge */}
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-extrabold text-gray-950 dark:text-white">
                            {t.name}
                          </span>
                          {t.isDefault && (
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-orange-100 text-[#FF551F] dark:bg-orange-950/60 dark:text-orange-300">
                              DEFAULT
                            </span>
                          )}
                        </div>
                        {isSelected && (
                          <div className="w-5 h-5 rounded-full bg-[var(--theme-primary)] text-white flex items-center justify-center shrink-0 shadow-xs">
                            <Check className="w-3 h-3 stroke-[3]" />
                          </div>
                        )}
                      </div>

                      {/* Swatch Previews: Accent Color over Base Background Color */}
                      <div className="flex items-center gap-2 my-2.5">
                        {/* Upper Color (Primary / Accent) */}
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700">
                          <span
                            className="w-3.5 h-3.5 rounded-full shadow-2xs"
                            style={{ backgroundColor: t.primary }}
                          />
                          <span className="text-[10px] font-mono font-bold text-gray-700 dark:text-gray-300">
                            {t.primary}
                          </span>
                        </div>

                        {/* Lower Color (Background / Base) */}
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700">
                          <span
                            className="w-3.5 h-3.5 rounded-full border border-gray-300 dark:border-zinc-600 shadow-2xs"
                            style={{ backgroundColor: t.baseBg }}
                          />
                          <span className="text-[10px] font-mono font-bold text-gray-700 dark:text-gray-300">
                            {t.baseBg}
                          </span>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-[11px] text-gray-500 dark:text-gray-400 font-medium leading-relaxed">
                        {t.description}
                      </p>
                    </div>

                    {/* Footer State */}
                    <div className="pt-2.5 mt-2 border-t border-gray-100 dark:border-zinc-700/60 flex items-center justify-between text-[10px] font-bold">
                      <span className={isSelected ? 'text-[var(--theme-primary)]' : 'text-gray-400'}>
                        {isSelected ? 'Currently Applied' : 'Click to apply'}
                      </span>
                      <div
                        className="w-12 h-2 rounded-full"
                        style={{
                          background: `linear-gradient(90deg, ${t.primary} 0%, ${t.baseBg} 100%)`,
                        }}
                      />
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="p-3.5 rounded-xl bg-gray-50/70 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800 text-xs text-gray-600 dark:text-gray-400 flex items-center gap-2">
              <span className="font-bold text-gray-900 dark:text-white">Note:</span>
              <span>Theme preference is stored locally on this workstation and automatically restores on future visits. Default fallback is always Orange.</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Garages / Branches */}
      {showNonThemeTabs && visibleTab === 'garages-branches' && (
        <div className="space-y-4">
          <div className="dashboard-card-solid rounded-[24px] overflow-hidden">
            <div className="p-4 px-5 border-b border-[#f0e7df] dark:border-zinc-800 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-gray-950 dark:text-white">
                  Active Workshop Locations
                </h3>
                <p className="text-[11px] text-gray-500">
                  Branches registered for operational accounting and inventory tracking.
                </p>
              </div>
              <button
                onClick={() => onOpenFormModal('garage')}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#18181b] hover:bg-black text-white text-xs font-bold transition cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
                <span>Add Branch</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#f0e7df] dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/30">
                    <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Branch Name</th>
                    <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Location</th>
                    <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Vehicles Hosted</th>
                    <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase">Status</th>
                    <th className="py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f5ede5] dark:divide-zinc-800/60">
                  {data.garages.map((g) => {
                    const vehCount = (data.vehicles || []).filter((v) => v.garageId === g.id).length;
                    return (
                      <tr key={g.id} className="hover:bg-gray-50/70 dark:hover:bg-zinc-800/40">
                        <td className="py-3 px-4 font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                          <Building2 className="w-3.5 h-3.5 text-gray-400" />
                          <span>{g.name}</span>
                        </td>
                        <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{g.location}</td>
                        <td className="py-3 px-4 font-mono font-medium">{vehCount} vehicles</td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                              g.active
                                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                                : 'bg-gray-100 text-gray-600 dark:bg-zinc-800 dark:text-gray-400'
                            }`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full ${g.active ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                            <span>{g.active ? 'Active Branch' : 'Inactive'}</span>
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right space-x-2">
                          <button
                            onClick={() => handleToggleGarageStatus(g.id)}
                            className="text-[11px] font-bold text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white transition cursor-pointer"
                          >
                            {g.active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => onOpenFormModal('garageEdit', { garageId: g.id })}
                            className="text-[11px] font-bold text-[var(--theme-primary)] hover:underline transition cursor-pointer"
                          >
                            Edit
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Demo Data */}
      {showNonThemeTabs && visibleTab === 'demo-data' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Vehicles', count: data.vehicles.length },
              { label: 'Jobs', count: data.jobs.length },
              { label: 'Investors', count: data.investors.length },
              { label: 'Batches', count: data.batches.length },
              { label: 'Expenses', count: data.expenses.length },
              { label: 'Sales', count: data.sales.length },
              { label: 'Payments', count: data.payments.length },
              { label: 'Audit Records', count: data.audit.length },
            ].map((stat, i) => (
              <div key={i} className="dashboard-card-solid rounded-[20px] p-3.5">
                <span className="text-[11px] font-medium text-gray-500 block">{stat.label}</span>
                <span className="text-xl font-bold font-mono text-gray-950 dark:text-white mt-1 block">
                  {stat.count}
                </span>
              </div>
            ))}
          </div>

          <div className="dashboard-card-solid rounded-[24px] p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-950 dark:text-white">
              Data Persistence & Reset Controls
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
              Export current session data as a JSON snapshot, import a saved state, or reset to clean VIRMS seed records.
            </p>

            <div className="flex items-center gap-3 flex-wrap pt-2">
              <button
                onClick={handleExportJson}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-white dark:bg-zinc-800 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50 text-xs font-bold text-gray-800 dark:text-gray-200 shadow-2xs transition cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 text-blue-500" />
                <span>Export Snapshot (JSON)</span>
              </button>

              <button
                onClick={() => setShowImportArea(!showImportArea)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-white dark:bg-zinc-800 border border-[#e2d8ce] dark:border-zinc-700 hover:bg-gray-50 text-xs font-bold text-gray-800 dark:text-gray-200 shadow-2xs transition cursor-pointer"
              >
                <Upload className="w-3.5 h-3.5 text-emerald-500" />
                <span>Import Snapshot</span>
              </button>

              <button
                onClick={handleResetSeed}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 hover:bg-red-100 text-xs font-bold text-red-700 dark:text-red-300 shadow-2xs transition cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5 text-red-600" />
                <span>Reset to Seed Data</span>
              </button>
            </div>

            {showImportArea && (
              <div className="pt-4 border-t border-[#f0e7df] dark:border-zinc-800 space-y-3">
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">
                  Paste JSON Snapshot:
                </label>
                <textarea
                  rows={5}
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                  placeholder="Paste JSON content here..."
                  className="w-full p-3 rounded-xl border border-[#e2d8ce] dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 text-xs font-mono"
                />
                <button
                  onClick={handleImportJson}
                  className="px-4 py-2 rounded-full bg-[#18181b] text-white text-xs font-bold"
                >
                  Apply Imported Data
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
