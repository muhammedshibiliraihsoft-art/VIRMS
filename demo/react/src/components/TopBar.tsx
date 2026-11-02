import React, { useState } from 'react';
import {
  Search,
  Bell,
  RefreshCw,
  Sun,
  Moon,
  ChevronDown,
  Check,
  Menu,
} from 'lucide-react';
import { Garage } from '../types';

export interface TopBarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  garages: Garage[];
  selectedGarage: string;
  onSelectGarage: (garageId: string) => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  onOpenSearch?: () => void;
  onOpenMobileMenu?: () => void;
  loginId?: string;
  companyName?: string;
  companyWideRoles?: string[];
  branchNames?: string[];
  branchesTruncated?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  activeTab,
  onSelectTab,
  garages,
  selectedGarage,
  onSelectGarage,
  theme,
  onToggleTheme,
  onRefresh,
  isRefreshing = false,
  onOpenSearch,
  onOpenMobileMenu,
  loginId = '',
  companyName = '',
  companyWideRoles = [],
  branchNames = [],
  branchesTruncated = false,
}) => {
  const [garageMenuOpen, setGarageMenuOpen] = useState(false);

  const tabs = [
    { key: 'Overview', label: 'Overview' },
    { key: 'Vehicles', label: 'Vehicles' },
    { key: 'Garage Jobs', label: 'Garage Jobs', shortLabel: 'Jobs' },
    { key: 'Inventory', label: 'Inventory' },
    { key: 'Investor Fund', label: 'Investor Fund', shortLabel: 'Fund' },
    { key: 'Accounting', label: 'Accounting' },
    { key: 'Reports', label: 'Reports' },
  ];

  const currentGarageName =
    selectedGarage === 'all'
      ? 'All Garages'
      : garages.find((g) => g.id === selectedGarage)?.name || 'Central Garage';

  return (
    <header className="flex items-center justify-between w-full h-11 pb-1 select-none">
      {/* 1. Left: Mobile Menu Button + Brand Identity */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-1.5 rounded-xl text-gray-600 hover:text-black dark:text-gray-300 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800 transition cursor-pointer"
          aria-label="Open mobile navigation menu"
        >
          <Menu className="w-4 h-4" />
        </button>

        {/* Brand Icon Badge */}
        <div
          title="VIRMS"
          className="w-8 h-8 rounded-full bg-[var(--theme-primary)] flex items-center justify-center shadow-xs text-white font-extrabold text-sm tracking-tight shrink-0 transition-colors"
        >
          V
        </div>

        {/* Company Identity Label */}
        <div className="flex items-baseline gap-1">
          <span className="font-extrabold text-base tracking-tight text-gray-950 dark:text-white">
            VIRMS
          </span>
          <span className="hidden 2xl:inline text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
            Operations
          </span>
        </div>
      </div>

      {/* 2. Center: Reusable Navigation Tabs (Hidden on small viewports) */}
      <nav
        aria-label="Quick section navigation"
        className="hidden md:flex items-center gap-1 overflow-x-auto scrollbar-none px-1"
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onSelectTab(tab.key)}
              className={`px-3 py-1.5 rounded-full text-[11px] font-semibold transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-[#18181b] text-white shadow-xs dark:bg-white dark:text-black'
                  : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800'
              }`}
            >
              {tab.shortLabel ? (
                <>
                  <span className="hidden xl:inline">{tab.label}</span>
                  <span className="xl:hidden">{tab.shortLabel}</span>
                </>
              ) : (
                tab.label
              )}
            </button>
          );
        })}
      </nav>

      {/* 3. Right: Utility Controls, Theme, Refresh & Garage Filter */}
      <div className="flex items-center gap-1.5 shrink-0">
        {/* Search Action */}
        <button
          onClick={onOpenSearch}
          title="Search"
          aria-label="Search"
          className="w-8 h-8 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-700 transition cursor-pointer shadow-2xs"
        >
          <Search className="w-3.5 h-3.5" />
        </button>

        {/* Refresh Action with Truthful Local Reload State */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          title={isRefreshing ? 'Refreshing data...' : 'Refresh prototype data'}
          aria-label="Refresh data"
          className={`w-8 h-8 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-700 transition cursor-pointer shadow-2xs ${
            isRefreshing ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-[var(--theme-primary)]' : ''}`} />
        </button>

        {/* Global Theme Selector (Light / Dark) */}
        <button
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
          className="w-8 h-8 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-700 transition cursor-pointer shadow-2xs"
        >
          {theme === 'light' ? (
            <Moon className="w-3.5 h-3.5 text-zinc-600" />
          ) : (
            <Sun className="w-3.5 h-3.5 text-amber-400" />
          )}
        </button>

        {/* Notifications Indicator */}
        <button
          title="Notifications"
          aria-label="Notifications"
          className="relative hidden sm:flex w-8 h-8 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-700 transition cursor-pointer shadow-2xs"
        >
          <Bell className="w-3.5 h-3.5" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[var(--theme-primary)] ring-2 ring-white dark:ring-zinc-800" />
        </button>

        {/* Garage Filter Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setGarageMenuOpen(!garageMenuOpen)}
            aria-expanded={garageMenuOpen}
            aria-haspopup="true"
            aria-label={`Filter prototype garage data. Current: ${currentGarageName}. Signed in as ${loginId || 'user'}. Company: ${companyName || 'unavailable'}.`}
            title={`Signed in as ${loginId || 'user'} · Company: ${companyName || 'unavailable'}`}
            className="flex items-center gap-2 pl-1 pr-2.5 py-1 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 hover:border-gray-300 dark:hover:border-zinc-600 transition cursor-pointer shadow-2xs"
          >
            <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-stone-800 to-stone-600 text-white flex items-center justify-center text-[9px] font-bold overflow-hidden shrink-0">
              OP
            </div>
            <div className="text-left hidden md:block">
              <div className="text-[10px] font-bold text-gray-900 dark:text-white leading-tight">
                {currentGarageName}
              </div>
              <div className="text-[8px] text-gray-400 dark:text-gray-500 leading-tight hidden xl:block">
                {loginId || 'Signed in'}
              </div>
            </div>
            <ChevronDown className="w-3 h-3 text-gray-400 shrink-0" />
          </button>

          {/* Garage Dropdown Menu */}
          {garageMenuOpen && (
            <div
              role="menu"
              className="absolute right-0 mt-2 w-56 bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-gray-100 dark:border-zinc-800 p-1.5 z-50 animate-in fade-in zoom-in-95 duration-100"
            >
              {companyName && (
                <div className="border-b border-gray-100 px-3 pb-2 pt-1 dark:border-zinc-800">
                  <div className="text-[9px] font-bold uppercase tracking-wider text-gray-400">Company</div>
                  <div className="truncate text-xs font-semibold text-gray-800 dark:text-gray-100" title={companyName}>{companyName}</div>
                  {companyWideRoles.length > 0 && (
                    <div className="mt-0.5 truncate text-[10px] text-gray-500 dark:text-gray-400" title={companyWideRoles.join(', ')}>
                      Company-wide roles: {companyWideRoles.join(', ')}
                    </div>
                  )}
                  <div className="mt-0.5 truncate text-[10px] text-gray-500 dark:text-gray-400" title={branchNames.join(', ')}>
                    Branch context: {branchNames.length ? branchNames.slice(0, 3).join(', ') : 'no summaries returned'}
                  </div>
                  {(branchNames.length > 3 || branchesTruncated) && (
                    <div className="text-[10px] text-gray-500 dark:text-gray-400">More Branch context is available.</div>
                  )}
                </div>
              )}
              <div className="px-3 py-1.5 text-[9px] font-bold uppercase tracking-wider text-gray-400">
                Prototype garage filter
              </div>
              <button
                role="menuitem"
                onClick={() => {
                  onSelectGarage('all');
                  setGarageMenuOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-1.5 text-xs font-semibold rounded-xl text-left transition cursor-pointer ${
                  selectedGarage === 'all'
                    ? 'bg-gray-100 dark:bg-zinc-800 text-black dark:text-white font-bold'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-800/50'
                }`}
              >
                <span>All Garages (Consolidated)</span>
                {selectedGarage === 'all' && <Check className="w-3.5 h-3.5 text-[var(--theme-primary)]" />}
              </button>
              {garages.map((g) => (
                <button
                  key={g.id}
                  role="menuitem"
                  onClick={() => {
                    onSelectGarage(g.id);
                    setGarageMenuOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-1.5 text-xs font-semibold rounded-xl text-left transition cursor-pointer ${
                    selectedGarage === g.id
                      ? 'bg-gray-100 dark:bg-zinc-800 text-black dark:text-white font-bold'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-800/50'
                  }`}
                >
                  <div>
                    <div>{g.name}</div>
                    <div className="text-[10px] text-gray-400 font-normal">{g.location}</div>
                  </div>
                  {selectedGarage === g.id && <Check className="w-3.5 h-3.5 text-[var(--theme-primary)]" />}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
