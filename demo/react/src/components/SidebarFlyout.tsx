import React from 'react';
import {
  Car,
  Wrench,
  Package,
  Users,
  Folder,
  BarChart3,
  Settings,
  ChevronDown,
  ChevronRight,
  Dot,
  CheckCircle2,
  Clock,
  AlertCircle,
  Home,
} from 'lucide-react';
import { NavGroup, NavChildItem } from '../data/navigationRegistry';
import { DemoBadge } from './shared/DemoBadge';

interface SidebarFlyoutProps {
  group: NavGroup;
  allGroups: NavGroup[];
  activeRoute: string;
  isPinned: boolean;
  onSelectRoute: (routeKey: string) => void;
  onSelectGroup: (groupId: string) => void;
  onClose: () => void;
}

export const SidebarFlyout: React.FC<SidebarFlyoutProps> = ({
  group,
  allGroups,
  activeRoute,
  isPinned,
  onSelectRoute,
  onSelectGroup,
  onClose,
}) => {
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
    <div
      role="region"
      aria-label={`${group.label} submenu`}
      className="w-64 bg-white dark:bg-zinc-900 border border-gray-200/90 dark:border-zinc-800 rounded-[22px] p-3 shadow-xl shadow-black/8 z-50 flex flex-col gap-1.5 animate-in fade-in zoom-in-95 duration-100"
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      {/* Flyout Header */}
      <div
        onClick={() => {
          if (group.id === 'vehicles') {
            onSelectRoute('All Vehicles');
            onClose();
          } else if (group.primaryRouteKey) {
            onSelectRoute(group.primaryRouteKey);
            onClose();
          }
        }}
        className="flex items-center justify-between px-3 py-2 border-b border-gray-100 dark:border-zinc-800/80 cursor-pointer hover:bg-gray-50 dark:hover:bg-zinc-800/50 rounded-xl transition group/hdr"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-gray-700 dark:text-gray-300">
            {getIcon(group.iconName, 'w-4 h-4 text-[var(--theme-primary)]')}
          </span>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-gray-900 dark:text-white tracking-tight group-hover/hdr:text-[var(--theme-primary)] transition-colors">
              {group.label}
            </span>
            {group.id === 'vehicles' && (
              <span className="text-[10px] text-gray-400 dark:text-gray-500 font-medium leading-none mt-0.5">
                Open All Vehicles
              </span>
            )}
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          title={isPinned ? 'Unpin menu' : 'Close menu'}
          className="p-1 rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-zinc-800 transition cursor-pointer"
        >
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Children List */}
      <div className="flex flex-col gap-1 py-1">
        {group.children.map((child: NavChildItem) => {
          const isActive = activeRoute === child.routeKey;
          return (
            <button
              key={child.id}
              onClick={() => {
                onSelectRoute(child.routeKey);
                onClose();
              }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-xs font-semibold transition cursor-pointer group ${
                isActive
                  ? 'bg-[var(--theme-primary-soft)] text-gray-950 dark:text-white border border-[var(--theme-primary-border)] shadow-2xs font-bold'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/80 dark:hover:bg-zinc-800/60'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${isActive ? 'bg-[var(--theme-primary)]' : 'bg-gray-300 dark:bg-zinc-600'}`} />
                <div className="truncate">
                  <div className="truncate leading-tight">{child.label}</div>
                  {child.description && (
                    <div className="text-[10px] text-gray-400 dark:text-gray-500 font-normal truncate mt-0.5">
                      {child.description}
                    </div>
                  )}
                </div>
              </div>

              {/* Status Chips */}
              <div className="shrink-0 ml-1.5 flex items-center gap-1.5">
                {(child.dataSourceStatus ?? group.dataSourceStatus) === 'demo' && (
                  <DemoBadge size="compact" />
                )}
                {child.status === 'implemented' ? (
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" title="Implemented" />
                ) : child.status === 'read_only_by_business_rule' ? (
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200/60">
                    Notice
                  </span>
                ) : (
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-gray-100 text-gray-500 dark:bg-zinc-800 dark:text-gray-400">
                    Pending
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Other Groups (Accordion section if pinned, matching image 3 & 4) */}
      {isPinned && (
        <div className="mt-1 pt-2 border-t border-gray-100 dark:border-zinc-800/80 flex flex-col gap-0.5">
          {allGroups
            .filter((g) => g.id !== group.id && g.id !== 'dashboard')
            .slice(0, 4)
            .map((other) => (
              <button
                key={other.id}
                onClick={() => onSelectGroup(other.id)}
                className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-left text-xs font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-zinc-800/40 transition cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  {getIcon(other.iconName, 'w-3.5 h-3.5 text-gray-400')}
                  <span>{other.label}</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
              </button>
            ))}
        </div>
      )}
    </div>
  );
};
