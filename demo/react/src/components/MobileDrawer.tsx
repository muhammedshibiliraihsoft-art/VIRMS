import React, { useState } from 'react';
import {
  X,
  ChevronDown,
  ChevronRight,
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
} from 'lucide-react';
import { navigationRegistry, NavGroup } from '../data/navigationRegistry';

interface MobileDrawerProps {
  isOpen: boolean;
  activeRoute: string;
  onClose: () => void;
  onSelectRoute: (routeKey: string) => void;
  onOpenHelp: () => void;
  onLogout: () => void;
}

export const MobileDrawer: React.FC<MobileDrawerProps> = ({
  isOpen,
  activeRoute,
  onClose,
  onSelectRoute,
  onOpenHelp,
  onLogout,
}) => {
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['vehicles']);

  if (!isOpen) return null;

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) =>
      prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId]
    );
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
    <div className="fixed inset-0 z-50 lg:hidden flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel (Image 6 style) */}
      <div className="relative w-72 max-w-[85vw] bg-white dark:bg-zinc-900 h-full p-5 shadow-2xl flex flex-col justify-between z-10 overflow-y-auto">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-zinc-800">
            <div className="flex items-center gap-2">
              <span className="text-[var(--theme-primary)] font-black tracking-tighter text-lg">//</span>
              <span className="font-extrabold text-base tracking-tight text-gray-950 dark:text-white">
                VIRMS
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-full text-gray-400 hover:text-black dark:hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Groups Accordion */}
          <div className="mt-4 flex flex-col gap-1">
            {navigationRegistry.map((group) => {
              const isExpanded = expandedGroups.includes(group.id);
              const isDashboard = group.id === 'dashboard';

              if (isDashboard) {
                const isActive = activeRoute === 'Dashboard';
                return (
                  <button
                    key={group.id}
                    onClick={() => {
                      onSelectRoute('Dashboard');
                      onClose();
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left text-xs font-bold transition ${
                      isActive
                        ? 'bg-purple-50 text-purple-950 dark:bg-purple-950/40 dark:text-purple-300'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-800/60'
                    }`}
                  >
                    {getIcon(group.iconName)}
                    <span>Dashboard</span>
                  </button>
                );
              }

              return (
                <div key={group.id} className="flex flex-col">
                  <div className="w-full flex items-center justify-between rounded-xl hover:bg-gray-50 dark:hover:bg-zinc-800/60 transition">
                    <button
                      onClick={() => {
                        if (group.id === 'vehicles') {
                          onSelectRoute('All Vehicles');
                          onClose();
                        } else if (group.primaryRouteKey) {
                          onSelectRoute(group.primaryRouteKey);
                          onClose();
                        }
                      }}
                      className="flex-1 flex items-center gap-3 px-3 py-2.5 text-left text-xs font-bold text-gray-800 dark:text-gray-200 cursor-pointer"
                    >
                      {getIcon(group.iconName)}
                      <span>{group.label}</span>
                    </button>
                    {group.children.length > 0 && (
                      <button
                        onClick={() => toggleGroup(group.id)}
                        aria-label={`Toggle ${group.label} sub-items`}
                        className="p-2.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition cursor-pointer"
                      >
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}
                  </div>

                  {/* Children Submenu */}
                  {isExpanded && (
                    <div className="pl-9 pr-2 py-1 flex flex-col gap-1 border-l-2 border-gray-100 dark:border-zinc-800 ml-5 my-1">
                      {group.children.map((child) => {
                        const isChildActive = activeRoute === child.routeKey;
                        return (
                          <button
                            key={child.id}
                            onClick={() => {
                              onSelectRoute(child.routeKey);
                              onClose();
                            }}
                            className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition ${
                              isChildActive
                                ? 'bg-purple-100 text-purple-950 font-bold dark:bg-purple-950 dark:text-purple-300'
                                : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="truncate">{child.label}</span>
                              {child.status === 'pending' && (
                                <span className="text-[9px] text-gray-400 font-normal">
                                  Pending
                                </span>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Drawer Actions */}
        <div className="pt-4 border-t border-gray-100 dark:border-zinc-800 flex flex-col gap-1 text-xs font-semibold text-gray-600 dark:text-gray-400">
          <button
            onClick={() => {
              onOpenHelp();
              onClose();
            }}
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-zinc-800 transition"
          >
            <HelpCircle className="w-4 h-4" />
            <span>Help & Support</span>
          </button>
          <button
            onClick={() => {
              onLogout();
              onClose();
            }}
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition"
          >
            <LogOut className="w-4 h-4" />
            <span>Log Out</span>
          </button>
        </div>
      </div>
    </div>
  );
};
