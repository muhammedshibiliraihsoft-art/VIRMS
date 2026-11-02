import React, { useState, useRef, useEffect } from 'react';
import {
  Home,
  Car,
  Wrench,
  Package,
  Users,
  Folder,
  BarChart3,
  Settings,
  HelpCircle,
  LogOut,
  Sun,
  Moon,
} from 'lucide-react';
import type { NavGroup } from '../data/navigationRegistry';
import { SidebarFlyout } from './SidebarFlyout';

interface SidebarRailProps {
  navigationGroups: NavGroup[];
  activeRoute: string;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onSelectRoute: (routeKey: string) => void;
  onOpenHelp: () => void;
  onLogout: () => void;
}

export const SidebarRail: React.FC<SidebarRailProps> = ({
  navigationGroups,
  activeRoute,
  theme,
  onToggleTheme,
  onSelectRoute,
  onOpenHelp,
  onLogout,
}) => {
  const [hoveredGroupId, setHoveredGroupId] = useState<string | null>(null);
  const [pinnedGroupId, setPinnedGroupId] = useState<string | null>(null);
  const [flyoutTop, setFlyoutTop] = useState<number>(60);
  const railRef = useRef<HTMLDivElement>(null);
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const activeGroup =
    navigationGroups.find(
      (g) =>
        g.primaryRouteKey === activeRoute ||
        (g.id === 'vehicles' && (activeRoute === 'Vehicles' || activeRoute === 'All Vehicles' || activeRoute === 'Vehicle Detail')) ||
        (g.id === 'garage-operations' && (activeRoute === 'Garage Jobs' || activeRoute === 'Garage Job Detail')) ||
        g.children.some((c) => c.routeKey === activeRoute)
    );

  const currentOpenGroupId = pinnedGroupId || hoveredGroupId;
  const currentOpenGroup = navigationGroups.find((g) => g.id === currentOpenGroupId);
  const hasDashboard = navigationGroups.some((group) => group.id === 'dashboard');
  const settingsGroup = navigationGroups.find((group) => group.id === 'settings');
  const primaryGroups = navigationGroups.filter((group) => group.id !== 'settings');

  // Close flyout on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (railRef.current && !railRef.current.contains(e.target as Node)) {
        setPinnedGroupId(null);
        setHoveredGroupId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMouseEnter = (groupId: string, event: React.MouseEvent<HTMLButtonElement>) => {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    const rect = event.currentTarget.getBoundingClientRect();
    const railTop = railRef.current?.getBoundingClientRect().top || 16;
    const buttonTop = rect.top - railTop;
    setFlyoutTop(Math.max(8, Math.min(buttonTop - 4, window.innerHeight - railTop - 340)));
    setHoveredGroupId(groupId);
  };

  const handleMouseLeave = () => {
    if (pinnedGroupId) return;
    hoverTimeoutRef.current = setTimeout(() => {
      setHoveredGroupId(null);
    }, 200);
  };

  const handleClickGroup = (group: NavGroup, event: React.MouseEvent<HTMLButtonElement>) => {
    if (group.id === 'dashboard') {
      onSelectRoute('Dashboard');
      setPinnedGroupId(null);
      setHoveredGroupId(null);
      return;
    }

    if (group.id === 'vehicles') {
      onSelectRoute(group.primaryRouteKey);
    }

    if (group.id === 'garage-operations') {
      onSelectRoute('Garage Jobs');
      setPinnedGroupId(null);
      setHoveredGroupId(null);
      return;
    }

    if (group.id === 'settings') {
      onSelectRoute(group.primaryRouteKey);
      setPinnedGroupId(null);
      setHoveredGroupId(null);
      return;
    }

    const rect = event.currentTarget.getBoundingClientRect();
    const railTop = railRef.current?.getBoundingClientRect().top || 16;
    const buttonTop = rect.top - railTop;
    setFlyoutTop(Math.max(8, Math.min(buttonTop - 4, window.innerHeight - railTop - 340)));

    if (pinnedGroupId === group.id) {
      setPinnedGroupId(null);
    } else {
      setPinnedGroupId(group.id);
      setHoveredGroupId(null);
    }
  };

  const getIcon = (name: string, className = 'w-4 h-4') => {
    switch (name) {
      case 'Home':
        return <Home className={className} />;
      case 'Car':
        return <Car className={className} />;
      case 'Wrench':
        return <Wrench className={className} />;
      case 'Package':
        return <Package className={className} />;
      case 'Users':
        return <Users className={className} />;
      case 'Folder':
        return <Folder className={className} />;
      case 'BarChart3':
        return <BarChart3 className={className} />;
      case 'Settings':
        return <Settings className={className} />;
      default:
        return <Folder className={className} />;
    }
  };

  return (
    <aside
      ref={railRef}
      aria-label="Sidebar Navigation"
      className="hidden lg:flex fixed top-3 sm:top-4 lg:top-5 bottom-3 sm:bottom-4 lg:bottom-5 z-40 select-none flex-col items-center w-[58px] sm:w-[62px]"
      style={{
        height: 'calc(100dvh - 32px)',
        maxHeight: 'calc(100dvh - 32px)',
        left: 'clamp(16px, 2vw, 32px)',
      }}
      onMouseLeave={handleMouseLeave}
    >
      {/* Sleek, Narrow 58px–62px Navigation Rail */}
      <div className="w-full bg-[#18181b] text-white rounded-[24px] px-1.5 py-3 sm:py-3.5 flex flex-col items-center shadow-lg shadow-black/8 h-full border border-zinc-800/90">

        {/* Zone 1: Compact Top Logo (~36px) */}
        <div className="flex flex-col items-center">
          {hasDashboard ? (
            <button
              type="button"
              title="VIRMS Operations"
              aria-label="Open Dashboard"
              className="w-9 h-9 rounded-xl bg-white/10 hover:bg-white/15 flex items-center justify-center transition cursor-pointer"
              onClick={() => onSelectRoute('Dashboard')}
            >
              <span className="text-[var(--theme-primary)] font-black tracking-tighter text-base transition-colors">//</span>
            </button>
          ) : (
            <div
              title="VIRMS Operations"
              aria-hidden="true"
              className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center"
            >
              <span className="text-[var(--theme-primary)] font-black tracking-tighter text-base transition-colors">//</span>
            </div>
          )}

          <div className="w-6 h-[1px] bg-zinc-800/90 mt-2.5 mb-2" />
        </div>

        {/* Zone 2: Primary Navigation Group (Compact Stack with 10–12px gaps) */}
        <nav
          className="flex flex-col items-center gap-2.5 w-full pt-0.5"
          aria-label="Main Navigation Rail"
        >
          {primaryGroups.map((group) => {
            const isGroupActive = activeGroup?.id === group.id;
            const isOpen = currentOpenGroupId === group.id;

            return (
              <div key={group.id} className="relative group/tooltip flex items-center justify-center">
                <button
                  onClick={(e) => handleClickGroup(group, e)}
                  onMouseEnter={(e) => handleMouseEnter(group.id, e)}
                  aria-label={group.label}
                  aria-expanded={isOpen}
                  className={`w-[38px] h-[38px] sm:w-[40px] sm:h-[40px] rounded-xl flex items-center justify-center transition-all cursor-pointer ${
                    isGroupActive
                      ? 'bg-white text-black shadow-xs font-semibold'
                      : isOpen
                      ? 'bg-zinc-700/80 text-white'
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-800/70'
                  }`}
                >
                  {getIcon(group.iconName, 'w-[18px] h-[18px]')}
                </button>

                {/* Accessible Hover Tooltip when flyout is closed */}
                {!currentOpenGroupId && (
                  <div className="absolute left-[48px] top-1/2 -translate-y-1/2 px-2.5 py-1 bg-black text-white text-[11px] font-semibold rounded-lg shadow-md whitespace-nowrap opacity-0 pointer-events-none group-hover/tooltip:opacity-100 transition-opacity z-50">
                    {group.label}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* Spacer pushing utilities cleanly to bottom without stretching navigation */}
        <div className="flex-1 min-h-6" />

        {/* Zone 3: Compact Bottom Utilities with subtle divider */}
        <div className="flex flex-col items-center gap-2 w-full pt-2 border-t border-zinc-800/90">
          {/* Settings */}
          {settingsGroup && (
            <div className="relative group/tooltip flex items-center justify-center">
              <button
                onClick={(e) => handleClickGroup(settingsGroup, e)}
                onMouseEnter={(e) => handleMouseEnter('settings', e)}
                title="Settings"
                aria-label="Settings"
                className={`w-[38px] h-[38px] sm:w-[40px] sm:h-[40px] rounded-xl flex items-center justify-center transition-all cursor-pointer ${
                  activeGroup?.id === 'settings'
                    ? 'bg-white text-black shadow-xs font-semibold'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800/70'
                }`}
              >
                <Settings className="w-[18px] h-[18px]" />
              </button>
              {!currentOpenGroupId && (
                <div className="absolute left-[48px] top-1/2 -translate-y-1/2 px-2 py-0.5 bg-black text-white text-[10px] font-semibold rounded shadow whitespace-nowrap opacity-0 pointer-events-none group-hover/tooltip:opacity-100 transition-opacity z-50">
                  Settings
                </div>
              )}
            </div>
          )}

          {/* Theme Toggle Sun / Moon */}
          <button
            onClick={onToggleTheme}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            className="w-[38px] h-[38px] sm:w-[40px] sm:h-[40px] rounded-xl flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800/70 transition cursor-pointer"
          >
            {theme === 'light' ? <Moon className="w-[17px] h-[17px]" /> : <Sun className="w-[17px] h-[17px] text-amber-400" />}
          </button>

          {/* Help */}
          <button
            onClick={onOpenHelp}
            title="Help & Support"
            className="w-[38px] h-[38px] sm:w-[40px] sm:h-[40px] rounded-xl flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800/70 transition cursor-pointer"
          >
            <HelpCircle className="w-[18px] h-[18px]" />
          </button>

          {/* Log Out */}
          <button
            onClick={onLogout}
            title="Log Out"
            className="w-[38px] h-[38px] sm:w-[40px] sm:h-[40px] rounded-xl flex items-center justify-center text-zinc-400 hover:text-rose-400 hover:bg-zinc-800/70 transition cursor-pointer"
          >
            <LogOut className="w-[18px] h-[18px]" />
          </button>
        </div>
      </div>

      {/* Nested Flyout Panel (240px wide, positioned adjacent to the rail) */}
      {currentOpenGroup && currentOpenGroup.id !== 'dashboard' && (
        <div
          className="absolute left-[66px] sm:left-[70px] z-50 transition-all"
          style={{ top: `${flyoutTop}px` }}
          onMouseEnter={() => {
            if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
          }}
          onMouseLeave={handleMouseLeave}
        >
          <SidebarFlyout
            group={currentOpenGroup}
            allGroups={navigationGroups}
            activeRoute={activeRoute}
            isPinned={Boolean(pinnedGroupId)}
            onSelectRoute={(routeKey) => {
              onSelectRoute(routeKey);
              setPinnedGroupId(null);
              setHoveredGroupId(null);
            }}
            onSelectGroup={(groupId) => {
              setPinnedGroupId(groupId);
            }}
            onClose={() => {
              setPinnedGroupId(null);
              setHoveredGroupId(null);
            }}
          />
        </div>
      )}
    </aside>
  );
};
