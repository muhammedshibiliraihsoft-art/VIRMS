import React, { useState } from 'react';
import {
  LayoutDashboard,
  Wrench,
  BarChart3,
  TrendingUp,
  RefreshCw,
  Clock,
  ChevronDown,
  Check,
} from 'lucide-react';
import {
  DashboardViewId,
  AutoRefreshInterval,
  DASHBOARD_VIEWS,
} from '../../types/dashboard';

interface DashboardHeaderProps {
  userLabel?: string;
  activeView: DashboardViewId;
  onSelectView: (viewId: DashboardViewId) => void;
  lastFetchedAt?: number;
  isRefreshing: boolean;
  onRefreshActive: () => void;
  autoRefreshInterval: AutoRefreshInterval;
  onSelectAutoRefresh: (interval: AutoRefreshInterval) => void;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  userLabel,
  activeView,
  onSelectView,
  lastFetchedAt,
  isRefreshing,
  onRefreshActive,
  autoRefreshInterval,
  onSelectAutoRefresh,
}) => {
  const [autoRefreshOpen, setAutoRefreshOpen] = useState(false);

  const formatLastUpdated = (timeMs?: number) => {
    if (!timeMs) return 'Updated just now';
    const diffSec = Math.floor((Date.now() - timeMs) / 1000);
    if (diffSec < 10) return 'Updated just now';
    if (diffSec < 60) return `Updated ${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `Updated ${diffMin}m ago`;
    const date = new Date(timeMs);
    return `Updated at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  };

  const autoRefreshOptions: { label: string; value: AutoRefreshInterval }[] = [
    { label: 'Off', value: 0 },
    { label: 'Every 15 min', value: 15 },
    { label: 'Every 30 min', value: 30 },
    { label: 'Every 60 min', value: 60 },
  ];

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-3.5 pt-0.5 pb-1 select-none">
      {/* 1. Left: Greeting & Subtitle */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-xl sm:text-2xl lg:text-[26px] font-extrabold text-gray-950 dark:text-white tracking-tight">
            Good morning, {userLabel || 'there'}
          </h1>
          {!DASHBOARD_VIEWS[activeView]?.isBackendConnected && (
            <span className="px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase tracking-wider bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
              UI ONLY
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium">
          {DASHBOARD_VIEWS[activeView]?.description || 'Stay on top of your tasks, monitor progress, and track status.'}
        </p>
      </div>

      {/* 2. Right: Dashboard Switcher & Live Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Switcher Pill Group - 4 Switchable Dashboards */}
        <div
          role="tablist"
          aria-label="Dashboard perspective switcher"
          className="flex items-center p-1 rounded-full bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10"
        >
          {/* View 1: Overview (Official Default) */}
          <button
            role="tab"
            aria-selected={activeView === 'overview'}
            onClick={() => onSelectView('overview')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              activeView === 'overview'
                ? 'bg-white dark:bg-zinc-800 text-gray-950 dark:text-white shadow-2xs font-extrabold'
                : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
            <span>Overview</span>
          </button>

          {/* View 2: Operations */}
          <button
            role="tab"
            aria-selected={activeView === 'operations'}
            onClick={() => onSelectView('operations')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              activeView === 'operations'
                ? 'bg-white dark:bg-zinc-800 text-gray-950 dark:text-white shadow-2xs font-extrabold'
                : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'
            }`}
          >
            <Wrench className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
            <span>Operations</span>
          </button>

          {/* View 3: Analytics */}
          <button
            role="tab"
            aria-selected={activeView === 'analytics'}
            onClick={() => onSelectView('analytics')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              activeView === 'analytics'
                ? 'bg-white dark:bg-zinc-800 text-gray-950 dark:text-white shadow-2xs font-extrabold'
                : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
            <span>Analytics</span>
          </button>

          {/* View 4: Financial */}
          <button
            role="tab"
            aria-selected={activeView === 'financial'}
            onClick={() => onSelectView('financial')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition cursor-pointer ${
              activeView === 'financial'
                ? 'bg-white dark:bg-zinc-800 text-gray-950 dark:text-white shadow-2xs font-extrabold'
                : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
            <span>Financial</span>
          </button>
        </div>

        {/* Live Status and Update Button */}
        <div className="flex items-center gap-1.5">
          {/* Update Dashboard Action */}
          <button
            onClick={onRefreshActive}
            disabled={isRefreshing}
            title="Refresh only currently active dashboard"
            aria-label="Update active dashboard"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 hover:border-gray-300 dark:hover:border-zinc-600 text-xs font-semibold text-gray-700 dark:text-gray-200 transition cursor-pointer shadow-2xs ${
              isRefreshing ? 'opacity-60 cursor-not-allowed' : ''
            }`}
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${
                isRefreshing ? 'animate-spin text-[var(--theme-primary)]' : 'text-gray-500'
              }`}
            />
            <span className="hidden sm:inline">Update</span>
          </button>

          {/* Auto Refresh Dropdown */}
          <div className="relative">
            <button
              onClick={() => setAutoRefreshOpen(!autoRefreshOpen)}
              title="Configure auto-refresh interval for active view"
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 hover:border-gray-300 dark:hover:border-zinc-600 text-xs font-semibold text-gray-700 dark:text-gray-300 transition cursor-pointer shadow-2xs"
            >
              <Clock className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-[11px]">
                {autoRefreshInterval === 0 ? 'Manual' : `${autoRefreshInterval}m`}
              </span>
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>

            {autoRefreshOpen && (
              <div
                role="menu"
                className="absolute right-0 mt-1.5 w-36 bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-gray-100 dark:border-zinc-800 p-1 z-50 animate-in fade-in zoom-in-95 duration-100"
              >
                <div className="px-2.5 py-1 text-[9px] font-bold uppercase tracking-wider text-gray-400">
                  Auto Refresh
                </div>
                {autoRefreshOptions.map((opt) => (
                  <button
                    key={opt.value}
                    role="menuitem"
                    onClick={() => {
                      onSelectAutoRefresh(opt.value);
                      setAutoRefreshOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 text-xs font-medium rounded-xl text-left transition cursor-pointer ${
                      autoRefreshInterval === opt.value
                        ? 'bg-gray-100 dark:bg-zinc-800 text-black dark:text-white font-bold'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-800/50'
                    }`}
                  >
                    <span>{opt.label}</span>
                    {autoRefreshInterval === opt.value && (
                      <Check className="w-3 h-3 text-[var(--theme-primary)]" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Last Updated Timestamp */}
          <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium pl-1 hidden lg:inline">
            {formatLastUpdated(lastFetchedAt)}
          </span>
        </div>
      </div>
    </div>
  );
};
