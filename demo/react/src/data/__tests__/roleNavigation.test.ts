import { describe, expect, it } from 'vitest';
import {
  canPresentBusinessWriteActions,
  getInitialDashboardView,
  getRoleDashboardViews,
  getRoleNavigation,
  getRoleQuickSections,
  isInvestorOnlyRole,
  isRoleRouteVisible,
} from '../roleNavigation';
import { navigationRegistry } from '../navigationRegistry';

const groupIds = (roles: readonly string[] | undefined) =>
  getRoleNavigation(roles).map((group) => group.id);

const routeKeys = (roles: readonly string[] | undefined) =>
  getRoleNavigation(roles).flatMap((group) => group.children.map((child) => child.routeKey));

describe('role-based navigation presentation', () => {
  it('presents ordinary business write actions only for a Company-wide Accountant role', () => {
    expect(canPresentBusinessWriteActions(['accountant'])).toBe(true);
    expect(canPresentBusinessWriteActions(['owner'])).toBe(false);
    expect(canPresentBusinessWriteActions(['investor'])).toBe(false);
    expect(canPresentBusinessWriteActions(['media'])).toBe(false);
    expect(canPresentBusinessWriteActions(['back_office'])).toBe(false);
    expect(canPresentBusinessWriteActions(undefined)).toBe(false);
  });

  it('shows V2 Accountant operations while keeping unsupported inventory and platform/demo settings out', () => {
    expect(groupIds(['accountant'])).toEqual([
      'dashboard',
      'vehicles',
      'garage-operations',
      'investment-management',
      'company-accounting',
      'reports',
      'settings',
    ]);
    expect(routeKeys(['accountant'])).toContain('Sale Corrections & Refunds');
    expect(routeKeys(['accountant'])).toContain('Owner Distribution');
    expect(routeKeys(['accountant'])).toContain('Appearance & Theme');
    expect(routeKeys(['accountant'])).not.toContain('Items & Purchases');
    expect(routeKeys(['accountant'])).not.toContain('Stock Issues');
    expect(routeKeys(['accountant'])).not.toContain('Stock Reports');
    expect(routeKeys(['accountant'])).not.toContain('Product Margin');
    expect(routeKeys(['accountant'])).not.toContain('Garages / Branches');
    expect(routeKeys(['accountant'])).not.toContain('Demo Data');
  });

  it('limits Owner navigation to V2 Company-wide read and audit areas', () => {
    expect(groupIds(['owner'])).toEqual([
      'dashboard',
      'vehicles',
      'garage-operations',
      'investment-management',
      'company-accounting',
      'reports',
      'settings',
    ]);
    expect(routeKeys(['owner'])).toContain('Company Result');
    expect(routeKeys(['owner'])).toContain('Owner Distribution');
    expect(routeKeys(['owner'])).toContain('Audit & Corrections');
    expect(routeKeys(['owner'])).not.toContain('Sale Corrections & Refunds');
    expect(routeKeys(['owner'])).not.toContain('Product Margin');
    expect(routeKeys(['owner'])).not.toContain('Stock Issues');
  });

  it('shows only Investor areas named by V2 and does not show Company finance or reports', () => {
    expect(groupIds(['investor'])).toEqual([
      'dashboard',
      'vehicles',
      'investment-management',
      'settings',
    ]);
    expect(routeKeys(['investor'])).toEqual([
      'Dashboard',
      'Stock / Investor',
      'Investor Fund',
      'Investor Profit & Interim',
      'Reconciliation & Settlement',
      'Appearance & Theme',
    ]);
  });

  it('does not expose unrelated business pages to Media when no media-specific route exists', () => {
    expect(groupIds(['media'])).toEqual(['settings']);
    expect(routeKeys(['media'])).toEqual(['Appearance & Theme']);
  });

  it('unions Company-wide roles and ignores unknown/global roles', () => {
    expect(groupIds(['owner', 'accountant'])).not.toContain('inventory');
    expect(groupIds(['back_office'])).toEqual([]);
    expect(groupIds(['future_role'])).toEqual([]);
    expect(groupIds(undefined)).toEqual([]);
  });

  it('keeps quick section tabs within the role-filtered navigation', () => {
    const ownerNavigation = getRoleNavigation(['owner']);
    expect(getRoleQuickSections(ownerNavigation).map((section) => section.key)).toEqual([
      'Overview',
      'Vehicles',
      'Garage Jobs',
      'Investor Fund',
      'Accounting',
      'Reports',
    ]);
    expect(getRoleQuickSections(getRoleNavigation(['media']))).toEqual([]);
  });

  it('keeps detail routes within their role-visible parent modules', () => {
    expect(isRoleRouteVisible(getRoleNavigation(['owner']), 'Vehicle Detail', ['owner'])).toBe(true);
    expect(isRoleRouteVisible(getRoleNavigation(['owner']), 'Garage Job Detail')).toBe(true);
    expect(isRoleRouteVisible(getRoleNavigation(['investor']), 'Garage Job Detail')).toBe(false);
    expect(isRoleRouteVisible(getRoleNavigation(['future_role']), 'Dashboard')).toBe(false);
    expect(isRoleRouteVisible(getRoleNavigation(['investor']), 'Vehicle Detail')).toBe(false);
    expect(isRoleRouteVisible(getRoleNavigation(['investor']), 'Vehicle Detail', ['investor'])).toBe(false);
    expect(isRoleRouteVisible(getRoleNavigation(['owner', 'investor']), 'Vehicle Detail', ['owner', 'investor'])).toBe(true);
  });

  it('keeps vehicle and settings shortcuts aligned with visible role routes', () => {
    const owner = getRoleNavigation(['owner']);
    const investor = getRoleNavigation(['investor']);
    expect(isRoleRouteVisible(owner, 'Vehicles', ['owner'])).toBe(true);
    expect(isRoleRouteVisible(owner, 'All Vehicles', ['owner'])).toBe(true);
    expect(isRoleRouteVisible(owner, 'Settings', ['owner'])).toBe(true);
    expect(isRoleRouteVisible(investor, 'Vehicles', ['investor'])).toBe(true);
  });

  it('limits Investor dashboard subviews and rejects direct Company dashboard URLs', () => {
    expect(getRoleDashboardViews(['investor'])).toEqual(['overview']);
    expect(getInitialDashboardView('?view=financial', ['investor'])).toBe('overview');
    expect(getInitialDashboardView('?view=operations', ['investor'])).toBe('overview');
    expect(getRoleDashboardViews(['owner'])).toEqual(['overview', 'operations', 'analytics', 'financial']);
    expect(getInitialDashboardView('?view=financial', ['accountant'])).toBe('financial');
    expect(isInvestorOnlyRole(['investor'])).toBe(true);
    expect(isInvestorOnlyRole(['owner', 'investor'])).toBe(false);
  });

  it('blocks direct UI route selection for unsupported Inventory routes', () => {
    for (const role of ['accountant', 'owner']) {
      const navigation = getRoleNavigation([role]);
      for (const route of ['Inventory', 'Items & Purchases', 'Stock Issues', 'Stock Reports', 'Product Margin']) {
        expect(isRoleRouteVisible(navigation, route), `${role} should not see ${route}`).toBe(false);
      }
    }
  });

  it('returns filtered copies and leaves the shared navigation registry unchanged', () => {
    const before = JSON.stringify(navigationRegistry);
    const navigation = getRoleNavigation(['owner']);
    navigation[0].children.pop();
    expect(JSON.stringify(navigationRegistry)).toBe(before);
  });
});
