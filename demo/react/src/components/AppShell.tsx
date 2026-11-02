import React, { useState } from 'react';
import { SidebarRail } from './SidebarRail';
import { MobileDrawer } from './MobileDrawer';
import { TopBar } from './TopBar';
import { StatusMessageLayer } from './StatusMessageLayer';
import { Garage } from '../types';
import { StatusMessage } from '../types/statusMessage';
import { getRoleNavigation } from '../data/roleNavigation';
import { getRouteDataSourceStatus } from '../data/navigationRegistry';
import type { BranchSummary } from '../api/types';
import { DemoBadge } from './shared/DemoBadge';

export interface AppShellProps {
  children: React.ReactNode;
  activeRoute: string;
  activeTab: string;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onSelectRoute: (routeKey: string) => void;
  onSelectTab: (tabKey: string) => void;
  garages: Garage[];
  selectedGarage: string;
  onSelectGarage: (garageId: string) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  statusMessages: StatusMessage[];
  onDismissStatus: (id: string) => void;
  onOpenSearch?: () => void;
  onOpenHelp?: () => void;
  onLogout?: () => void;
  loginId?: string;
  companyName?: string;
  companyWideRoles?: string[];
  branchContexts?: BranchSummary[];
  branchesTruncated?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeRoute,
  activeTab,
  theme,
  onToggleTheme,
  onSelectRoute,
  onSelectTab,
  garages,
  selectedGarage,
  onSelectGarage,
  onRefresh,
  isRefreshing = false,
  statusMessages,
  onDismissStatus,
  onOpenSearch,
  onOpenHelp,
  onLogout,
  loginId,
  companyName,
  companyWideRoles,
  branchContexts,
  branchesTruncated,
}) => {
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const navigationGroups = getRoleNavigation(companyWideRoles);
  const showDemoPageBadge =
    activeRoute !== 'Dashboard' &&
    activeRoute !== 'Overview' &&
    getRouteDataSourceStatus(activeRoute) === 'demo';

  return (
    <div data-theme={theme} className={theme === 'dark' ? 'dark' : ''}>
      <div className="app-shell text-[#18181b] dark:text-gray-100 flex flex-col w-full transition-colors duration-200 min-h-screen min-h-[100dvh]">

        {/* Responsive Full-Width Main Workspace Container */}
        <div
          className="w-full flex-1 flex items-stretch relative"
          style={{
            paddingInline: 'clamp(16px, 2vw, 32px)',
            paddingBlock: 'clamp(16px, 1.5vw, 24px)',
            gap: 'clamp(14px, 1.8vw, 28px)',
          }}
        >
          {/* 1. Layout spacer to reserve sidebar width in normal flow so main does not move under it */}
          <div className="hidden lg:block w-[58px] sm:w-[62px] shrink-0" aria-hidden="true" />

          {/* 2. Modern Narrow 64px Navigation Rail with Nested Flyouts (Fixed to Viewport) */}
          <SidebarRail
            navigationGroups={navigationGroups}
            activeRoute={activeRoute}
            theme={theme}
            onToggleTheme={onToggleTheme}
            onSelectRoute={onSelectRoute}
            onOpenHelp={onOpenHelp || (() => {})}
            onLogout={onLogout || (() => {})}
          />

          {/* 3. Responsive Mobile Drawer Navigation */}
          <MobileDrawer
            navigationGroups={navigationGroups}
            isOpen={mobileDrawerOpen}
            activeRoute={activeRoute}
            onClose={() => setMobileDrawerOpen(false)}
            onSelectRoute={onSelectRoute}
            onOpenHelp={onOpenHelp || (() => {})}
            onLogout={onLogout || (() => {})}
          />

          {/* 4. Main Workspace Column: Takes full remaining height and pushes footer cleanly to bottom */}
          <div className="flex-1 min-w-0 flex flex-col self-stretch">
            {/* Shared Reusable TopBar */}
            <TopBar
              activeTab={activeTab}
              onSelectTab={onSelectTab}
              garages={garages}
              selectedGarage={selectedGarage}
              onSelectGarage={onSelectGarage}
              theme={theme}
              onToggleTheme={onToggleTheme}
              onRefresh={onRefresh}
              isRefreshing={isRefreshing}
              mobileDrawerOpen={mobileDrawerOpen}
              onOpenSearch={onOpenSearch}
              onOpenMobileMenu={() => setMobileDrawerOpen(true)}
              loginId={loginId}
              companyName={companyName}
              companyWideRoles={companyWideRoles}
              navigationGroups={navigationGroups}
              branchContexts={branchContexts}
              branchesTruncated={branchesTruncated}
            />

            {/* Main Content Area: flex-1 expands to fill available vertical space */}
            <main className="flex-1 min-w-0 flex flex-col gap-3.5 sm:gap-4.5 pt-3 sm:pt-3.5">
              {showDemoPageBadge && (
                <div className="flex justify-end">
                  <DemoBadge />
                </div>
              )}
              {children}
            </main>

            {/* 5. Minimal Subtle Footer: mt-auto ensures it sits at bottom on short pages, follows content on long pages */}
            <footer className="mt-auto pt-8 pb-2 border-t border-gray-200/50 dark:border-zinc-800/60 flex flex-col sm:flex-row items-center justify-between text-[11px] text-gray-400 dark:text-gray-500 gap-2 select-none">
              <div className="flex items-center gap-1.5 font-medium">
                <span className="font-bold text-gray-700 dark:text-gray-300">VIRMS</span>
                <span>Operations Suite · v2.4</span>
                <span>·</span>
                <span>Prototype Workspace</span>
              </div>
              <div>
                Synthetic demo dataset · Business records preserved
              </div>
            </footer>
          </div>
        </div>

        {/* 6. Shared Global Status Message Notification Layer */}
        <StatusMessageLayer
          messages={statusMessages}
          onDismiss={onDismissStatus}
        />
      </div>
    </div>
  );
};
