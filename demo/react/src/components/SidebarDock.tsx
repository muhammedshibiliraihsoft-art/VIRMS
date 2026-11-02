import React from 'react';
import {
  Sun,
  Moon,
  Home,
  LayoutGrid,
  Mail,
  SlidersHorizontal,
  Users,
  Bell,
  Settings,
  HelpCircle,
  LogOut,
} from 'lucide-react';

interface SidebarDockProps {
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  activeNav: string;
  onSelectNav: (nav: string) => void;
}

export const SidebarDock: React.FC<SidebarDockProps> = ({
  theme,
  onToggleTheme,
  activeNav,
  onSelectNav,
}) => {
  return (
    <aside className="hidden lg:flex flex-col items-center justify-between py-2 w-14 shrink-0 z-20">
      {/* Top: Theme Toggle Pill (Exact style from Image 2) */}
      <div className="bg-white/90 dark:bg-zinc-850/90 border border-gray-200/90 dark:border-zinc-700/80 rounded-full p-1 flex flex-col items-center gap-1 shadow-2xs">
        <button
          onClick={onToggleTheme}
          aria-label="Light mode"
          className={`w-7 h-7 rounded-full flex items-center justify-center transition-all cursor-pointer ${
            theme === 'light'
              ? 'bg-[#18181b] text-white shadow-xs'
              : 'text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }`}
        >
          <Sun className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onToggleTheme}
          aria-label="Dark mode"
          className={`w-7 h-7 rounded-full flex items-center justify-center transition-all cursor-pointer ${
            theme === 'dark'
              ? 'bg-[#18181b] text-white shadow-xs'
              : 'text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }`}
        >
          <Moon className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Middle: Main Navigation Dock (Exact style from Image 2) */}
      <div className="bg-white/90 dark:bg-zinc-850/90 border border-gray-200/90 dark:border-zinc-700/80 rounded-[24px] p-1.5 flex flex-col items-center gap-1.5 shadow-2xs my-auto">
        <button
          onClick={() => onSelectNav('Overview')}
          title="Overview / Dashboard"
          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
            activeNav === 'Overview'
              ? 'bg-[#18181b] text-white shadow-xs'
              : 'text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700'
          }`}
        >
          <Home className="w-4 h-4" />
        </button>

        <button
          onClick={() => onSelectNav('Vehicles')}
          title="Vehicle Register"
          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
            activeNav === 'Vehicles'
              ? 'bg-[#18181b] text-white shadow-xs'
              : 'text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700'
          }`}
        >
          <LayoutGrid className="w-4 h-4" />
        </button>

        <button
          onClick={() => onSelectNav('Garage Jobs')}
          title="Garage Jobs & Work"
          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
            activeNav === 'Garage Jobs'
              ? 'bg-[#18181b] text-white shadow-xs'
              : 'text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700'
          }`}
        >
          <Mail className="w-4 h-4" />
        </button>

        <button
          onClick={() => onSelectNav('Investor Fund')}
          title="Investors & Fund"
          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
            activeNav === 'Investor Fund'
              ? 'bg-[#18181b] text-white shadow-xs'
              : 'text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700'
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
        </button>

        <button
          onClick={() => onSelectNav('Messages')}
          title="Notifications & Alerts"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700 transition cursor-pointer"
        >
          <Users className="w-4 h-4" />
        </button>

        <button
          onClick={() => onSelectNav('Activity')}
          title="Activity Log"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700 transition cursor-pointer"
        >
          <Bell className="w-4 h-4" />
        </button>

        <button
          onClick={() => onSelectNav('Settings')}
          title="Settings"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700 transition cursor-pointer"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>

      {/* Bottom: Help & Logout */}
      <div className="bg-white/90 dark:bg-zinc-850/90 border border-gray-200/90 dark:border-zinc-700/80 rounded-[24px] p-1.5 flex flex-col items-center gap-1.5 shadow-2xs">
        <button
          title="Help & Support"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-700 transition cursor-pointer"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
        <button
          title="Log Out"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-gray-500 hover:text-rose-600 dark:text-gray-400 dark:hover:text-rose-400 hover:bg-gray-100 dark:hover:bg-zinc-700 transition cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
