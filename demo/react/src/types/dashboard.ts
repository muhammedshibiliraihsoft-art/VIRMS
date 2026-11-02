export type DashboardViewId = 'overview' | 'operations' | 'analytics' | 'financial';

export type AutoRefreshInterval = 0 | 15 | 30 | 60; // in minutes (0 = Off)

export interface DashboardCacheEntry<T = any> {
  viewId: DashboardViewId;
  garageId: string;
  data: T;
  lastFetchedAt: number; // epoch ms
  status: 'idle' | 'loading' | 'success' | 'error';
}

export interface DashboardViewMeta {
  id: DashboardViewId;
  label: string;
  shortLabel: string;
  description: string;
  isBackendConnected: boolean; // false shows subtle 'UI ONLY' badge
}

export const DASHBOARD_VIEWS: Record<DashboardViewId, DashboardViewMeta> = {
  overview: {
    id: 'overview',
    label: 'Overview',
    shortLabel: 'Overview',
    description: 'Stay on top of your tasks, monitor progress, and track status.',
    isBackendConnected: true,
  },
  operations: {
    id: 'operations',
    label: 'Operations',
    shortLabel: 'Operations',
    description: 'Workshop capacity, job queues, vehicle intake & scheduler',
    isBackendConnected: true,
  },
  analytics: {
    id: 'analytics',
    label: 'Analytics',
    shortLabel: 'Analytics',
    description: 'Revenue realization curves, job execution funnel & advisor rankings',
    isBackendConnected: true,
  },
  financial: {
    id: 'financial',
    label: 'Financial',
    shortLabel: 'Financial',
    description: 'Commercial revenue, investor capital, receivables & deal register',
    isBackendConnected: true,
  },
};
