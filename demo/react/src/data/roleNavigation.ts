import type { NavGroup } from './navigationRegistry';
import { navigationRegistry } from './navigationRegistry';
import type { DashboardViewId } from '../types/dashboard';

type BusinessRole = 'owner' | 'accountant' | 'investor' | 'media';

type RoleNavigationPolicy = Partial<Record<string, readonly string[]>>;

export interface RoleQuickSection {
  key: string;
  label: string;
  shortLabel?: string;
}

interface QuickSectionDefinition extends RoleQuickSection {
  groupId: string;
}

const ROLE_NAVIGATION: Record<BusinessRole, RoleNavigationPolicy> = {
  accountant: {
    dashboard: ['Dashboard'],
    vehicles: ['Stock / Investor', 'Customer Vehicles'],
    'garage-operations': ['Garage Jobs'],
    'investment-management': [
      'Investor Fund',
      'Vehicle Sales',
      'Collections',
      'Sale Corrections & Refunds',
      'Investor Profit & Interim',
      'Reconciliation & Settlement',
    ],
    'company-accounting': [
      'Garage Revenue',
      'Company Income',
      'Company Expenses',
      'Running Capital',
      'Company Result',
      'Transactions',
      'Owner Distribution',
      'Audit & Corrections',
    ],
    reports: [
      'All Reports',
      'Company Consolidated',
      'Garage-wise',
      'Vehicle Cost',
      'Investor Fund Report',
      'Buyer Receivables',
    ],
    settings: ['Appearance & Theme'],
  },
  owner: {
    dashboard: ['Dashboard'],
    vehicles: ['Stock / Investor', 'Customer Vehicles'],
    'garage-operations': ['Garage Jobs'],
    'investment-management': [
      'Investor Fund',
      'Vehicle Sales',
      'Collections',
      'Investor Profit & Interim',
      'Reconciliation & Settlement',
    ],
    'company-accounting': [
      'Garage Revenue',
      'Company Income',
      'Company Expenses',
      'Running Capital',
      'Company Result',
      'Transactions',
      'Owner Distribution',
      'Audit & Corrections',
    ],
    reports: [
      'All Reports',
      'Company Consolidated',
      'Garage-wise',
      'Vehicle Cost',
      'Investor Fund Report',
      'Buyer Receivables',
    ],
    settings: ['Appearance & Theme'],
  },
  investor: {
    dashboard: ['Dashboard'],
    vehicles: ['Stock / Investor'],
    'investment-management': [
      'Investor Fund',
      'Investor Profit & Interim',
      'Reconciliation & Settlement',
    ],
    settings: ['Appearance & Theme'],
  },
  media: {
    settings: ['Appearance & Theme'],
  },
};

const QUICK_SECTIONS: QuickSectionDefinition[] = [
  { key: 'Overview', label: 'Overview', groupId: 'dashboard' },
  { key: 'Vehicles', label: 'Vehicles', groupId: 'vehicles' },
  { key: 'Garage Jobs', label: 'Garage Jobs', shortLabel: 'Jobs', groupId: 'garage-operations' },
  { key: 'Inventory', label: 'Inventory', groupId: 'inventory' },
  { key: 'Investor Fund', label: 'Investor Fund', shortLabel: 'Fund', groupId: 'investment-management' },
  { key: 'Accounting', label: 'Accounting', groupId: 'company-accounting' },
  { key: 'Reports', label: 'Reports', groupId: 'reports' },
] as const;

export function getRoleNavigation(companyWideRoles?: readonly string[]): NavGroup[] {
  const roles = (companyWideRoles ?? []).filter(
    (role): role is BusinessRole => Object.hasOwn(ROLE_NAVIGATION, role)
  );
  if (!roles.length) return [];

  const allowedRoutesByGroup = new Map<string, Set<string>>();
  for (const role of roles) {
    for (const [groupId, routeKeys] of Object.entries(ROLE_NAVIGATION[role])) {
      if (!routeKeys) continue;
      const allowedRoutes = allowedRoutesByGroup.get(groupId) ?? new Set<string>();
      routeKeys.forEach((routeKey) => allowedRoutes.add(routeKey));
      allowedRoutesByGroup.set(groupId, allowedRoutes);
    }
  }

  return navigationRegistry.flatMap((group) => {
    const allowedRoutes = allowedRoutesByGroup.get(group.id);
    if (!allowedRoutes) return [];
    const children = group.children
      .filter((child) => allowedRoutes.has(child.routeKey))
      .map((child) => ({ ...child }));
    if (!children.length) return [];
    return [{ ...group, children }];
  });
}

export function getRoleQuickSections(navigation: readonly NavGroup[]): RoleQuickSection[] {
  const visibleGroupIds = new Set(navigation.map((group) => group.id));
  return QUICK_SECTIONS
    .filter((section) => visibleGroupIds.has(section.groupId))
    .map(({ key, label, shortLabel }) =>
      shortLabel ? { key, label, shortLabel } : { key, label }
    );
}

export function canPresentBusinessWriteActions(companyWideRoles?: readonly string[]): boolean {
  return (companyWideRoles ?? []).includes('accountant');
}

export function isInvestorOnlyRole(companyWideRoles?: readonly string[]): boolean {
  const roles = companyWideRoles ?? [];
  return roles.includes('investor') && !roles.includes('owner') && !roles.includes('accountant');
}

export function getRoleDashboardViews(companyWideRoles?: readonly string[]): DashboardViewId[] {
  const roles = companyWideRoles ?? [];
  if (roles.includes('owner') || roles.includes('accountant')) {
    return ['overview', 'operations', 'analytics', 'financial'];
  }
  return roles.includes('investor') ? ['overview'] : [];
}

export function getInitialDashboardView(search: string, companyWideRoles?: readonly string[]): DashboardViewId {
  const allowedViews = getRoleDashboardViews(companyWideRoles);
  const requestedView = new URLSearchParams(search).get('view');
  return allowedViews.includes(requestedView as DashboardViewId)
    ? (requestedView as DashboardViewId)
    : 'overview';
}

export function isRoleRouteVisible(
  navigation: readonly NavGroup[],
  routeKey: string,
  companyWideRoles?: readonly string[]
): boolean {
  const visibleRouteKeys = new Set(navigation.flatMap((group) => group.children.map((child) => child.routeKey)));
  const visibleGroupIds = new Set(navigation.map((group) => group.id));
  if (routeKey === 'Overview') return visibleRouteKeys.has('Dashboard');
  if (routeKey === 'Vehicles' || routeKey === 'All Vehicles') return visibleGroupIds.has('vehicles');
  if (routeKey === 'Settings') return visibleGroupIds.has('settings');
  if (routeKey === 'Vehicle Detail') {
    if (!companyWideRoles || isInvestorOnlyRole(companyWideRoles)) return false;
    return visibleRouteKeys.has('Stock / Investor') || visibleRouteKeys.has('Customer Vehicles');
  }
  if (routeKey === 'Garage Job Detail') return visibleRouteKeys.has('Garage Jobs');
  return visibleRouteKeys.has(routeKey);
}
