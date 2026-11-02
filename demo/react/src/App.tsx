import React, { useState, useEffect } from 'react';
import { AppShell } from './components/AppShell';
import { RolePresentationProvider } from './auth/RolePresentationContext';
import {
  getInitialDashboardView,
  getRoleDashboardViews,
  getRoleNavigation,
  isInvestorOnlyRole,
  isRoleRouteVisible,
} from './data/roleNavigation';
import { PrimaryBalanceCard } from './components/PrimaryBalanceCard';
import { MetricGrid } from './components/MetricCard';
import { PerformanceChart } from './components/PerformanceChart';
import { InvestorUtilizationCard } from './components/InvestorUtilizationCard';
import { RecentActivityTable } from './components/RecentActivityTable';
import { DashboardHeader } from './components/dashboard/DashboardHeader';
import { DashboardSkeleton } from './components/dashboard/DashboardSkeleton';
import { DashboardOverviewView } from './components/dashboard/DashboardOverviewView';
import {
  DashboardViewId,
  AutoRefreshInterval,
  DASHBOARD_VIEWS,
} from './types/dashboard';
import {
  getCachedDashboardData,
  isDashboardCacheFresh,
  setCachedDashboardData,
  invalidateDashboardCache,
} from './services/dashboardCacheService';
import { QuickActionModal } from './components/QuickActionModal';

// Lazy loaded secondary dashboard views (chunks downloaded on demand only)
const DashboardOperationsView = React.lazy(
  () => import('./components/dashboard/DashboardOperationsView')
);
const DashboardAnalyticsView = React.lazy(
  () => import('./components/dashboard/DashboardAnalyticsView')
);
const DashboardFinancialView = React.lazy(
  () => import('./components/dashboard/DashboardFinancialView')
);
import { AllVehiclesView } from './components/AllVehiclesView';
import { VehicleDetailView } from './components/VehicleDetailView';
import { GarageJobsView } from './components/GarageJobsView';
import { GarageJobDetailView } from './components/GarageJobDetailView';
import { PendingViewPlaceholder } from './components/PendingViewPlaceholder';
import { NoticeView } from './components/shared/NoticeView';
import { ReportShell } from './components/shared/ReportShell';
import { FinancialLedgerView } from './components/shared/FinancialLedgerView';
import { InventoryWorkspaceView } from './components/shared/InventoryWorkspaceView';
import { CompanyResultView } from './components/shared/CompanyResultView';
import { SettingsAdminView } from './components/shared/SettingsAdminView';
import { SharedFormModal, FormModalType } from './components/shared/SharedFormModal';
import {
  getStoredThemePalette,
  setStoredThemePalette,
  applyThemePalette,
  THEME_REGISTRY,
} from './theme/themeRegistry';
import {
  initialData,
  initialGarages,
  initialInvestors,
  initialVehicles,
  initialJobs,
  initialBatches,
  initialSales,
  initialActivities,
} from './data/mockData';
import { ActivityItem, Job, Data, Vehicle } from './types';
import { StatusMessage, StatusMessageType } from './types/statusMessage';
import type { BranchSummary } from './api/types';

export interface AppProps {
  onLogout?: () => void;
  loginId?: string;
  companyName?: string;
  companyWideRoles?: string[];
  branchContexts?: BranchSummary[];
  branchesTruncated?: boolean;
}

export function App({ onLogout, loginId, companyName, companyWideRoles, branchContexts, branchesTruncated }: AppProps = {}) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [themePalette, setThemePalette] = useState<string>(getStoredThemePalette);
  const [activeRoute, setActiveRoute] = useState<string>(() =>
    getRoleNavigation(companyWideRoles)[0]?.children[0]?.routeKey ?? ''
  );
  const [activeTab, setActiveTab] = useState<string>('Overview');
  const [selectedGarage, setSelectedGarage] = useState<string>('all');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [statusMessages, setStatusMessages] = useState<StatusMessage[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [jobDetailOrigin, setJobDetailOrigin] = useState<'vehicle' | 'garage-jobs'>('garage-jobs');

  // Switchable Dashboard Views & Performance-Safe Cache State (Overview is official locked default)
  const [dashboardViewId, setDashboardViewId] = useState<DashboardViewId>(() =>
    getInitialDashboardView(window.location.search, companyWideRoles)
  );
  const [isRefreshingDashboard, setIsRefreshingDashboard] = useState<boolean>(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<AutoRefreshInterval>(0);
  const [cacheMeta, setCacheMeta] = useState<Record<DashboardViewId, { lastFetchedAt: number }>>({
    overview: { lastFetchedAt: Date.now() },
    operations: { lastFetchedAt: 0 },
    analytics: { lastFetchedAt: 0 },
    financial: { lastFetchedAt: 0 },
  });

  const handleSelectDashboardView = (view: DashboardViewId) => {
    if (!getRoleDashboardViews(companyWideRoles).includes(view)) return;
    setDashboardViewId(view);
    try {
      const url = new URL(window.location.href);
      if (view === 'overview') {
        url.searchParams.delete('view');
      } else {
        url.searchParams.set('view', view);
      }
      window.history.replaceState(null, '', url.pathname + (url.search ? url.search : ''));
    } catch {}

    // Check cache freshness for this view & garage
    const cached = getCachedDashboardData(view, selectedGarage);
    if (!cached || !isDashboardCacheFresh(cached)) {
      setCachedDashboardData(view, selectedGarage, { timestamp: Date.now() });
      setCacheMeta((prev) => ({
        ...prev,
        [view]: { lastFetchedAt: Date.now() },
      }));
    }
  };

  const handleRefreshActiveDashboard = async () => {
    if (!getRoleDashboardViews(companyWideRoles).includes(dashboardViewId)) return;
    if (isRefreshingDashboard) return;
    setIsRefreshingDashboard(true);
    invalidateDashboardCache(dashboardViewId, selectedGarage);
    await new Promise((r) => setTimeout(r, 450));
    setCachedDashboardData(dashboardViewId, selectedGarage, { timestamp: Date.now() });
    setCacheMeta((prev) => ({
      ...prev,
      [dashboardViewId]: { lastFetchedAt: Date.now() },
    }));
    setIsRefreshingDashboard(false);
    showStatusMessage(
      'info',
      'Prototype dashboard refreshed',
      'Displayed metrics are synthetic demo values, not live Company data.',
      4000
    );
  };

  // Synchronize active theme palette with root CSS tokens on mount and change
  useEffect(() => {
    applyThemePalette(themePalette);
  }, [themePalette]);

  const handleSelectThemePalette = (paletteId: string) => {
    setThemePalette(paletteId);
    setStoredThemePalette(paletteId);
    applyThemePalette(paletteId);
    const themeName = THEME_REGISTRY[paletteId]?.name ?? paletteId;
    showStatusMessage('success', `Theme switched to ${themeName}. System palette updated.`, undefined, 3000);
  };

  // Unified Canonical Demo Data State
  const [data, setData] = useState<Data>(initialData);
  const [activities, setActivities] = useState<ActivityItem[]>(initialActivities);

  // Modal State
  const [formModalState, setFormModalState] = useState<{
    isOpen: boolean;
    type: FormModalType | null;
    context?: Record<string, any>;
  }>({
    isOpen: false,
    type: null,
  });
  const roleNavigation = getRoleNavigation(companyWideRoles);
  const activeRouteAllowed = isRoleRouteVisible(roleNavigation, activeRoute, companyWideRoles);
  const investorOnly = isInvestorOnlyRole(companyWideRoles);
  const allowedDashboardViews = getRoleDashboardViews(companyWideRoles);
  const dashboardViewForRole = allowedDashboardViews.includes(dashboardViewId)
    ? dashboardViewId
    : 'overview';

  // Extract core entities for convenience
  const { garages, investors, vehicles, jobs, batches, sales } = data;

  // Status Message Helper
  const showStatusMessage = (
    type: StatusMessageType,
    message: string,
    description?: string,
    duration = 4000
  ) => {
    const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).substring(2, 6);
    const newMsg: StatusMessage = { id, type, message, description, duration };
    setStatusMessages((prev) => [...prev, newMsg]);

    if (duration > 0) {
      setTimeout(() => {
        setStatusMessages((prev) => prev.filter((m) => m.id !== id));
      }, duration);
    }
  };

  const handleDismissStatus = (id: string) => {
    setStatusMessages((prev) => prev.filter((m) => m.id !== id));
  };

  const handleLogout = async () => {
    if (!onLogout) {
      showStatusMessage('warning', 'Logged out of demo session', undefined, 3000);
      return;
    }
    try {
      await onLogout();
    } catch {
      showStatusMessage(
        'warning',
        'Sign out was not confirmed',
        'The session was rechecked. You are still signed in if the server confirms it.',
        6000
      );
    }
  };

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      showStatusMessage('info', `Switched to ${next} theme`, undefined, 2500);
      return next;
    });
  };

  const handleSelectRoute = (routeKey: string) => {
    if (!isRoleRouteVisible(roleNavigation, routeKey, companyWideRoles)) return;
    setActiveRoute(routeKey);
    if (routeKey !== 'Garage Job Detail') {
      setSelectedJobId(null);
    }
    if (routeKey !== 'Vehicle Detail') {
      setSelectedVehicleId(null);
    }
    if (routeKey === 'Dashboard' || routeKey === 'Overview') {
      setActiveTab('Overview');
      setDashboardViewId('overview');
      try {
        const url = new URL(window.location.href);
        url.searchParams.delete('view');
        window.history.replaceState(null, '', url.pathname + (url.search ? url.search : ''));
      } catch {}
    } else {
      setActiveTab(routeKey);
    }
    showStatusMessage('info', `Navigated to: ${routeKey}`, undefined, 2000);
  };

  const handleToggleJobStatus = (jobToToggle: Job) => {
    setData((prev) => ({
      ...prev,
      jobs: prev.jobs.map((j) =>
        j.id === jobToToggle.id
          ? {
              ...j,
              status: j.status === 'Open' ? 'Completed' : 'Open',
              statusHistory: [
                ...(j.statusHistory ?? []),
                {
                  id: 'sh-' + Date.now(),
                  timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
                  from: j.status,
                  to: j.status === 'Open' ? 'Completed' : 'Open',
                  actor: 'Demo Accountant',
                  note: 'Status toggled in demo session',
                },
              ],
            }
          : j
      ),
    }));
    showStatusMessage(
      'info',
      'Prototype job status changed locally only',
      `Job ${jobToToggle.number} was not saved to the VIRMS backend.`,
      5000
    );
  };

  const handleSelectGarage = (garageId: string) => {
    setSelectedGarage(garageId);
    const garageName =
      garageId === 'all'
        ? 'All Garages (Consolidated)'
        : garages.find((g) => g.id === garageId)?.name || 'Central Garage';
    showStatusMessage(
      'info',
      `Prototype garage filter: ${garageName}`,
      'This filters synthetic demo records only; it does not select an authorized Branch.',
      4000
    );
  };

  // Truthful prototype local data refresh
  const handleRefresh = async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    const loadingId = 'loading-' + Date.now();
    setStatusMessages((prev) => [
      ...prev,
      {
        id: loadingId,
        type: 'loading',
        message: 'Refreshing prototype data...',
        description: 'Re-syncing local dataset',
      },
    ]);

    await new Promise((resolve) => setTimeout(resolve, 400));
    setData(initialData);
    setActivities(initialActivities);

    setIsRefreshing(false);
    setStatusMessages((prev) => prev.filter((m) => m.id !== loadingId));
    showStatusMessage('success', 'Prototype data refreshed', 'Local records synchronized with baseline', 3000);
  };

  // Filter items by selected garage
  const filteredVehicles = vehicles.filter(
    (v) => selectedGarage === 'all' || v.garageId === selectedGarage
  );
  const filteredJobs = jobs.filter(
    (j) => selectedGarage === 'all' || j.garageId === selectedGarage
  );

  // Compute live dashboard metrics
  const activeStockVehicles = filteredVehicles.filter(
    (v) => v.type === 'Stock / Investor' && v.status !== 'Sold'
  );
  const totalStockCount = activeStockVehicles.length;
  const openJobsCount = filteredJobs.filter((j) => j.status === 'Open').length;

  const totalBuyerReceivable = sales.reduce((acc, s) => {
    const veh = vehicles.find((v) => v.id === s.vehicleId);
    if (selectedGarage !== 'all' && veh?.garageId !== selectedGarage) return acc;
    return acc + Math.max(0, s.price - s.received);
  }, 0);

  const inventoryStockValue = batches.reduce((acc, b) => {
    if (selectedGarage !== 'all' && b.garageId !== selectedGarage) return acc;
    return acc + b.quantity * b.cost;
  }, 0);

  const totalInvestorPrincipal = investors.reduce((acc, i) => acc + i.principal, 0);
  const totalInvestorUsed = investors.reduce((acc, i) => acc + (i.used || 0), 0);

  // Route Classification
  const isDashboardView = activeRoute === 'Dashboard' || activeRoute === 'Overview';
  const isVehicleDetailView = activeRoute === 'Vehicle Detail';
  const isGarageJobDetailView =
    activeRoute === 'Garage Job Detail' || (activeRoute === 'Garage Jobs' && selectedJobId !== null);
  const isGarageJobsView =
    (activeRoute === 'Garage Jobs' || activeTab === 'Garage Jobs') && !isGarageJobDetailView;
  const isVehiclesView =
    (activeRoute === 'Vehicles' ||
      activeRoute === 'All Vehicles' ||
      activeRoute === 'Stock / Investor' ||
      activeRoute === 'Customer Vehicles' ||
      activeTab === 'Vehicles') &&
    !isVehicleDetailView &&
    !isGarageJobsView &&
    !isGarageJobDetailView;

  // Auto-refresh active dashboard effect (Runs only for active dashboard when tab is visible)
  useEffect(() => {
    if (autoRefreshInterval === 0 || !isDashboardView) return;
    const intervalMs = autoRefreshInterval * 60 * 1000;
    const timer = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) return;
      handleRefreshActiveDashboard();
    }, intervalMs);
    return () => clearInterval(timer);
  }, [autoRefreshInterval, dashboardViewId, selectedGarage, isDashboardView]);

  // Selected Entities
  const selectedVehicle =
    vehicles.find((v) => v.id === selectedVehicleId) ||
    vehicles.find((v) => v.id === 'v-6') ||
    vehicles[0];

  const selectedJob =
    jobs.find((j) => j.id === selectedJobId) ||
    jobs.find((j) => j.number === 'JOB-1048') ||
    jobs[0];

  const jobVehicle =
    vehicles.find((v) => v.id === selectedJob?.vehicleId) || vehicles[0];

  const vehicleMode =
    activeRoute === 'Stock / Investor'
      ? 'stock-investor'
      : activeRoute === 'Customer Vehicles'
      ? 'customer'
      : 'all';

  return (
    <RolePresentationProvider companyWideRoles={companyWideRoles}>
    <AppShell
      activeRoute={activeRoute}
      activeTab={activeTab}
      theme={theme}
      onToggleTheme={toggleTheme}
      onSelectRoute={handleSelectRoute}
      onSelectTab={(tab) => {
        if (tab === 'Overview') {
          handleSelectRoute('Dashboard');
        } else if (tab === 'Accounting') {
          handleSelectRoute('Garage Revenue');
        } else if (tab === 'Inventory') {
          handleSelectRoute('Items & Purchases');
        } else if (tab === 'Reports') {
          handleSelectRoute('All Reports');
        } else {
          handleSelectRoute(tab);
        }
      }}
      garages={garages}
      selectedGarage={selectedGarage}
      onSelectGarage={handleSelectGarage}
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      statusMessages={statusMessages}
      onDismissStatus={handleDismissStatus}
      onOpenSearch={() => showStatusMessage('info', 'Global search opened', undefined, 2000)}
      onOpenHelp={() => showStatusMessage('info', 'VIRMS Documentation & User Guides', undefined, 3000)}
      onLogout={handleLogout}
      loginId={loginId}
      companyName={companyName}
      companyWideRoles={companyWideRoles}
      branchContexts={branchContexts}
      branchesTruncated={branchesTruncated}
    >
      {roleNavigation.length === 0 ? (
        <div role="status" className="rounded-xl border border-gray-200 dark:border-zinc-800 p-4 text-sm text-gray-600 dark:text-gray-300">
          No business workspace is available for this account.
        </div>
      ) : !activeRouteAllowed ? (
        <div role="status" className="rounded-xl border border-gray-200 dark:border-zinc-800 p-4 text-sm text-gray-600 dark:text-gray-300">
          This page is not available for the current Company role.
        </div>
      ) : isDashboardView && investorOnly ? (
        <PendingViewPlaceholder
          routeKey="Dashboard"
          onReturnToDashboard={() => handleSelectRoute('Dashboard')}
          descriptionOverride="Investor-specific dashboard data is not connected. Shared Company sample metrics are hidden."
          stateOverride="Waiting for an Investor-scoped data API; no shared Company sample data is shown."
        />
      ) : isDashboardView ? (
        <div className="space-y-4">
          {/* Centralized Switcher & Live Controls Header */}
          <DashboardHeader
            userLabel={loginId}
            activeView={dashboardViewForRole}
            availableViews={allowedDashboardViews}
            onSelectView={handleSelectDashboardView}
            lastFetchedAt={cacheMeta[dashboardViewForRole]?.lastFetchedAt}
            isRefreshing={isRefreshingDashboard}
            onRefreshActive={handleRefreshActiveDashboard}
            autoRefreshInterval={autoRefreshInterval}
            onSelectAutoRefresh={setAutoRefreshInterval}
          />

          {/* View 1: Official Approved Overview Dashboard (Image 1 Layout - Eagerly loaded default with 0 delay) */}
          {dashboardViewForRole === 'overview' && (
            <DashboardOverviewView
              totalBuyerReceivable={totalBuyerReceivable}
              investors={investors}
              stockVehiclesCount={totalStockCount}
              openJobsCount={openJobsCount}
              inventoryStockValue={inventoryStockValue}
              totalInvestorUsed={totalInvestorUsed}
              totalInvestorPrincipal={totalInvestorPrincipal}
              activities={activities}
              onRecordReceipt={() => setFormModalState({ isOpen: true, type: 'customerReceipt' })}
              onNewSale={() => setFormModalState({ isOpen: true, type: 'sale' })}
              onSelectActivity={(item) =>
                showStatusMessage('info', `Selected ${item.code}: ${item.title}`, undefined, 2500)
              }
            />
          )}

          {/* Secondary Views (Lazy-loaded on demand only) */}
          <React.Suspense fallback={<DashboardSkeleton />}>
            {dashboardViewForRole === 'operations' && (
              <DashboardOperationsView
                data={data}
                selectedGarage={selectedGarage}
                onOpenFormModal={(type, ctx) =>
                  setFormModalState({ isOpen: true, type, context: ctx })
                }
                onSelectRoute={handleSelectRoute}
              />
            )}
            {dashboardViewForRole === 'analytics' && (
              <DashboardAnalyticsView
                data={data}
                selectedGarage={selectedGarage}
                onSelectRoute={handleSelectRoute}
              />
            )}
            {dashboardViewForRole === 'financial' && (
              <DashboardFinancialView
                data={data}
                activities={activities}
                selectedGarage={selectedGarage}
                onOpenFormModal={(type, ctx) =>
                  setFormModalState({ isOpen: true, type, context: ctx })
                }
                onSelectRoute={handleSelectRoute}
                onSelectActivity={(item) =>
                  showStatusMessage('info', `Selected ${item.code}: ${item.title}`, undefined, 2500)
                }
              />
            )}
          </React.Suspense>
        </div>
      ) : isVehicleDetailView && selectedVehicle ? (
        /* Faithful Vehicle Detail View with Landscape Image Slot */
        <VehicleDetailView
          vehicle={selectedVehicle}
          garages={garages}
          jobs={jobs}
          data={data}
          onBack={() => {
            setSelectedVehicleId(null);
            handleSelectRoute(
              selectedVehicle.type === 'Customer' ? 'Customer Vehicles' : 'Stock / Investor'
            );
          }}
          onCreateJob={(veh) => {
            setFormModalState({
              isOpen: true,
              type: 'job',
              context: { vehicleId: veh.id, garageId: veh.garageId },
            });
          }}
          onAddExpense={(veh) => {
            setFormModalState({
              isOpen: true,
              type: 'vehicleExpense',
              context: { vehicleId: veh.id, garageId: veh.garageId },
            });
          }}
          onViewJobDetail={(job) => {
            setSelectedJobId(job.id);
            setJobDetailOrigin('vehicle');
            setActiveRoute('Garage Job Detail');
            showStatusMessage('info', `Job Detail: ${job.number}`, job.description, 3000);
          }}
        />
      ) : isGarageJobDetailView && selectedJob ? (
        /* Faithful Redesign of Garage Job Detail */
        <GarageJobDetailView
          job={selectedJob}
          vehicle={jobVehicle}
          garages={garages}
          data={data}
          selectedGarage={selectedGarage}
          onSelectGarage={handleSelectGarage}
          backLabel={
            jobDetailOrigin === 'vehicle' ? 'Back to Vehicle Workspace' : 'Back to Garage Jobs'
          }
          onBack={() => {
            setSelectedJobId(null);
            if (jobDetailOrigin === 'vehicle') {
              setActiveRoute('Vehicle Detail');
            } else {
              setActiveRoute('Garage Jobs');
            }
          }}
          onAddWork={(j) => {
            setFormModalState({
              isOpen: true,
              type: 'jobWork',
              context: { jobId: j.id, vehicleId: j.vehicleId },
            });
          }}
          onAddCostOrCharge={(j) => {
            if (jobVehicle.type === 'Customer') {
              setFormModalState({
                isOpen: true,
                type: 'customerCharge',
                context: { jobId: j.id, vehicleId: j.vehicleId },
              });
            } else {
              setFormModalState({
                isOpen: true,
                type: 'jobExpense',
                context: { jobId: j.id, vehicleId: j.vehicleId },
              });
            }
          }}
          onReceive={(j) => {
            setFormModalState({
              isOpen: true,
              type: 'customerReceipt',
              context: { jobId: j.id },
            });
          }}
          onToggleJobStatus={handleToggleJobStatus}
        />
      ) : isGarageJobsView ? (
        /* Work Queue List View */
        <GarageJobsView
          jobs={jobs}
          vehicles={vehicles}
          garages={garages}
          selectedGarage={selectedGarage}
          onSelectJob={(j) => {
            setSelectedJobId(j.id);
            setJobDetailOrigin('garage-jobs');
            setActiveRoute('Garage Job Detail');
          }}
          onNewJob={() => {
            setFormModalState({
              isOpen: true,
              type: 'job',
            });
          }}
          onAddWork={(j) => {
            setFormModalState({
              isOpen: true,
              type: 'jobWork',
              context: { jobId: j.id, vehicleId: j.vehicleId },
            });
          }}
          onAddCostOrCharge={(j) => {
            const v = vehicles.find((veh) => veh.id === j.vehicleId);
            if (v?.type === 'Customer') {
              setFormModalState({
                isOpen: true,
                type: 'customerCharge',
                context: { jobId: j.id, vehicleId: j.vehicleId },
              });
            } else {
              setFormModalState({
                isOpen: true,
                type: 'jobExpense',
                context: { jobId: j.id, vehicleId: j.vehicleId },
              });
            }
          }}
          onReceive={(j) => {
            setFormModalState({
              isOpen: true,
              type: 'customerReceipt',
              context: { jobId: j.id },
            });
          }}
          onToggleStatus={handleToggleJobStatus}
        />
      ) : isVehiclesView && investorOnly ? (
        <PendingViewPlaceholder
          routeKey="Stock / Investor"
          onReturnToDashboard={() => handleSelectRoute('Dashboard')}
          descriptionOverride="Investor-owned Stock Vehicles are not connected to an Investor-scoped API. Shared Company sample Vehicles are hidden."
          stateOverride="Waiting for Investor-scoped Vehicle data; no shared Company sample data is shown."
        />
      ) : isVehiclesView ? (
        /* Reusable Card-Based Vehicles View */
        <AllVehiclesView
          mode={vehicleMode}
          vehicles={vehicles}
          garages={garages}
          selectedGarage={selectedGarage}
          onSelectRoute={handleSelectRoute}
          onRegisterVehicle={() => setFormModalState({ isOpen: true, type: 'vehicle' })}
          onViewVehicleDetail={(veh) => {
            setSelectedVehicleId(veh.id);
            handleSelectRoute('Vehicle Detail');
          }}
        />
      ) : activeRoute === 'Investor Profit & Interim' ? (
        /* Notice View: BDR-01, BDR-02, BDR-03, BDR-04 */
        <NoticeView
          title="Investor Profit & Interim Distribution"
          category="INVESTMENT MANAGEMENT"
          bdrCodes={['BDR-01', 'BDR-02', 'BDR-03', 'BDR-04']}
          description="In accordance with the VIRMS V2 canonical specification, investor profit split calculations and interim dividend distributions are unapproved pending explicit shareholder consensus. To safeguard accounting integrity, no automated interim profit distributions are posted."
          reasons={[
            'BDR-01: Vehicle Profit Split Basis (Net sale vs cost basis formula unapproved)',
            'BDR-02: Loss Allocation Policy (Absorption of vehicle losses between investor & company)',
            'BDR-03: Interim Distribution Safeguard (Distribution before final buyer collection is barred)',
            'BDR-04: Multi-Vehicle Fund Pooling (Cross-collateralization across portfolio is locked)',
          ]}
          onExploreReports={investorOnly ? undefined : () => handleSelectRoute('Investor Fund Report')}
        />
      ) : activeRoute === 'Reconciliation & Settlement' ? (
        /* Notice View: BDR-05, BDR-06, BDR-07 */
        <NoticeView
          title="Reconciliation & Portfolio Settlement"
          category="INVESTMENT MANAGEMENT"
          bdrCodes={['BDR-05', 'BDR-06', 'BDR-07']}
          description="Final contract settlement and fund reconciliation are frozen in read-only mode until authorized governance policies are resolved by company stakeholders."
          reasons={[
            'BDR-05: Final Settlement Threshold (Clearance of outstanding buyer notes required)',
            'BDR-06: Escrow & Warranty Retention (Reserve holding period for buyer dispute warranty)',
            'BDR-07: Unilateral Capital Extraction (Principal withdrawals during open vehicle lifecycle barred)',
          ]}
          onExploreReports={investorOnly ? undefined : () => handleSelectRoute('Company Consolidated')}
        />
      ) : activeRoute === 'Owner Distribution' ? (
        /* Notice View: BDR-08 */
        <NoticeView
          title="Owner Distribution Governance"
          category="COMPANY ACCOUNTING"
          bdrCodes={['BDR-08']}
          description="Owner drawing rules, partner distributions and retainage reserves are held in canonical read-only state pending board ratification."
          reasons={[
            'BDR-08: Owner Drawing Schedule & Minimum Working Capital Thresholds',
          ]}
          onExploreReports={() => handleSelectRoute('Company Result')}
        />
      ) : activeRoute === 'Company Result' ? (
        /* Company Result Executive Overview */
        <CompanyResultView
          data={data}
          garages={garages}
          selectedGarage={selectedGarage}
          onSelectGarage={handleSelectGarage}
          onSelectRoute={handleSelectRoute}
        />
      ) : activeRoute === 'Items & Purchases' ||
        activeRoute === 'Stock Issues' ||
        activeRoute === 'Stock Reports' ||
        activeRoute === 'Inventory' ? (
        /* Inventory Workspace */
        <InventoryWorkspaceView
          initialTab={
            activeRoute === 'Stock Issues'
              ? 'stock-issues'
              : activeRoute === 'Stock Reports'
              ? 'stock-reports'
              : 'items-purchases'
          }
          data={data}
          garages={garages}
          selectedGarage={selectedGarage}
          onSelectGarage={handleSelectGarage}
          onOpenFormModal={(type, ctx) =>
            setFormModalState({ isOpen: true, type, context: ctx })
          }
        />
      ) : activeRoute === 'Investor Fund' && investorOnly ? (
        <PendingViewPlaceholder
          routeKey="Investor Fund"
          onReturnToDashboard={() => handleSelectRoute('Dashboard')}
          descriptionOverride="Investor-specific Fund data is not connected. Other Investors’ sample balances are hidden."
          stateOverride="Waiting for Investor-scoped Fund data; no other Investor sample records are shown."
        />
      ) : activeRoute === 'Investor Fund' ||
        activeRoute === 'Vehicle Sales' ||
        activeRoute === 'Collections' ||
        activeRoute === 'Sale Corrections & Refunds' ||
        activeRoute === 'Garage Revenue' ||
        activeRoute === 'Company Income' ||
        activeRoute === 'Company Expenses' ||
        activeRoute === 'Running Capital' ||
        activeRoute === 'Transactions' ||
        activeRoute === 'Audit & Corrections' ||
        activeRoute === 'Accounting' ? (
        /* Financial Ledgers & Registers */
        <FinancialLedgerView
          routeKey={activeRoute === 'Accounting' ? 'Garage Revenue' : activeRoute}
          data={data}
          garages={garages}
          selectedGarage={selectedGarage}
          onSelectGarage={handleSelectGarage}
          onOpenFormModal={(type, ctx) =>
            setFormModalState({ isOpen: true, type, context: ctx })
          }
        />
      ) : activeRoute === 'Garages / Branches' ||
        activeRoute === 'Demo Data' ||
        activeRoute === 'Appearance & Theme' ||
        activeRoute === 'Settings' ? (
        /* Settings & Branch Administration */
        <SettingsAdminView
          initialTab={
            activeRoute === 'Demo Data'
              ? 'demo-data'
              : activeRoute === 'Appearance & Theme' || activeRoute === 'Settings'
              ? 'theme-appearance'
              : 'garages-branches'
          }
          data={data}
          currentThemePalette={themePalette}
          onSelectThemePalette={handleSelectThemePalette}
          onUpdateData={setData}
          onOpenFormModal={(type, ctx) =>
            setFormModalState({ isOpen: true, type, context: ctx })
          }
          onSuccessMessage={(msg) => showStatusMessage('info', 'Prototype settings action completed locally', `${msg} No changes were saved to the VIRMS backend.`, 5000)}
          showNonThemeTabs={false}
        />
      ) : (
        /* Reports Shell (All Reports & 17 Operational Reports) */
        <ReportShell
          activeRoute={activeRoute}
          data={data}
          garages={garages}
          selectedGarage={selectedGarage}
          onSelectGarage={handleSelectGarage}
          onSelectRoute={handleSelectRoute}
        />
      )}

      {/* Shared Interactive Form Modal */}
      <SharedFormModal
        isOpen={formModalState.isOpen}
        type={formModalState.type}
        onClose={() => setFormModalState({ isOpen: false, type: null })}
        data={data}
        onUpdateData={setData}
        initialContext={formModalState.context}
        onSuccessMessage={(msg) => showStatusMessage('info', 'Prototype data changed locally only', `${msg} Not saved to the VIRMS backend.`, 5000)}
      />
    </AppShell>
    </RolePresentationProvider>
  );
}

export default App;
