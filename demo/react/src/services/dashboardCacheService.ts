import { DashboardViewId, DashboardCacheEntry } from '../types/dashboard';

export const DASHBOARD_CACHE_TTL_MS = 60 * 60 * 1000; // 1-Hour Frontend Cache freshness target

const inMemoryDashboardCache = new Map<string, DashboardCacheEntry>();

export function getDashboardCacheKey(viewId: DashboardViewId, garageId: string): string {
  return `dashboard:${viewId}:garage-${garageId || 'all'}`;
}

export function getCachedDashboardData<T>(viewId: DashboardViewId, garageId: string): DashboardCacheEntry<T> | null {
  const key = getDashboardCacheKey(viewId, garageId);
  const entry = inMemoryDashboardCache.get(key);
  if (!entry) return null;
  return entry as DashboardCacheEntry<T>;
}

export function isDashboardCacheFresh(entry: DashboardCacheEntry | null): boolean {
  if (!entry) return false;
  const now = Date.now();
  return now - entry.lastFetchedAt < DASHBOARD_CACHE_TTL_MS;
}

export function setCachedDashboardData<T>(viewId: DashboardViewId, garageId: string, data: T): DashboardCacheEntry<T> {
  const key = getDashboardCacheKey(viewId, garageId);
  const entry: DashboardCacheEntry<T> = {
    viewId,
    garageId: garageId || 'all',
    data,
    lastFetchedAt: Date.now(),
    status: 'success',
  };
  inMemoryDashboardCache.set(key, entry);
  return entry;
}

export function invalidateDashboardCache(viewId?: DashboardViewId, garageId?: string): void {
  if (viewId && garageId) {
    const key = getDashboardCacheKey(viewId, garageId);
    inMemoryDashboardCache.delete(key);
  } else if (viewId) {
    // Invalidate all garages for this specific view
    for (const key of inMemoryDashboardCache.keys()) {
      if (key.startsWith(`dashboard:${viewId}:`)) {
        inMemoryDashboardCache.delete(key);
      }
    }
  } else {
    // Clear entire cache
    inMemoryDashboardCache.clear();
  }
}
