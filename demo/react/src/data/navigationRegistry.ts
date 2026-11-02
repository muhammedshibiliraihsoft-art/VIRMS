export type NavItemStatus = 'implemented' | 'pending' | 'read_only_by_business_rule';
export type DataSourceStatus = 'backend' | 'demo';

export interface NavChildItem {
  id: string;
  label: string;
  routeKey: string;
  status: NavItemStatus;
  description?: string;
  badge?: string;
  dataSourceStatus?: DataSourceStatus;
}

export interface NavGroup {
  id: string;
  label: string;
  iconName: string;
  primaryRouteKey: string;
  status: NavItemStatus;
  dataSourceStatus: DataSourceStatus;
  children: NavChildItem[];
}

export const navigationRegistry: NavGroup[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    iconName: 'Home',
    primaryRouteKey: 'Dashboard',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'overview',
        label: 'Overview',
        routeKey: 'Dashboard',
        status: 'implemented',
        description: 'Cross-module overview & operational metrics',
      },
    ],
  },
  {
    id: 'vehicles',
    label: 'Vehicles',
    iconName: 'Car',
    primaryRouteKey: 'All Vehicles',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'stock-investor',
        label: 'Stock / Investor',
        routeKey: 'Stock / Investor',
        status: 'implemented',
        description: 'Stock vehicle register & purchases',
      },
      {
        id: 'customer-vehicles',
        label: 'Customer Vehicles',
        routeKey: 'Customer Vehicles',
        status: 'implemented',
        description: 'Customer registered vehicles & service intake',
      },
    ],
  },
  {
    id: 'garage-operations',
    label: 'Garage Operations',
    iconName: 'Wrench',
    primaryRouteKey: 'Garage Jobs',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'garage-jobs',
        label: 'Garage Jobs',
        routeKey: 'Garage Jobs',
        status: 'implemented',
        description: 'Work orders, job costs & stage tracking',
      },
    ],
  },
  {
    id: 'inventory',
    label: 'Inventory',
    iconName: 'Package',
    primaryRouteKey: 'Items & Purchases',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'items-purchases',
        label: 'Items & Purchases',
        routeKey: 'Items & Purchases',
        status: 'implemented',
        description: 'Item catalog & distinct purchase batches',
      },
      {
        id: 'stock-issues',
        label: 'Stock Issues',
        routeKey: 'Stock Issues',
        status: 'implemented',
        description: 'Issue parts to stock vehicle or customer job',
      },
      {
        id: 'stock-reports',
        label: 'Stock Reports',
        routeKey: 'Stock Reports',
        status: 'implemented',
        description: 'Stock valuation, batch remaining & product margin',
      },
    ],
  },
  {
    id: 'investment-management',
    label: 'Investment Management',
    iconName: 'Users',
    primaryRouteKey: 'Investor Fund',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'investor-fund',
        label: 'Investor Fund',
        routeKey: 'Investor Fund',
        status: 'implemented',
        description: 'Investor capital positions, reserves & history',
      },
      {
        id: 'vehicle-sales',
        label: 'Vehicle Sales',
        routeKey: 'Vehicle Sales',
        status: 'implemented',
        description: 'Sale agreements & agreed buyer prices',
      },
      {
        id: 'collections',
        label: 'Collections',
        routeKey: 'Collections',
        status: 'implemented',
        description: 'Actual buyer receipts & customer payments',
      },
      {
        id: 'sale-corrections-refunds',
        label: 'Sale Corrections & Refunds',
        routeKey: 'Sale Corrections & Refunds',
        status: 'implemented',
        description: 'Linked price corrections & actual buyer refunds',
      },
      {
        id: 'investor-profit-interim',
        label: 'Investor Profit & Interim',
        routeKey: 'Investor Profit & Interim',
        status: 'read_only_by_business_rule',
        description: 'Unapproved profit basis (Decision required)',
        badge: 'Read-only',
      },
      {
        id: 'reconciliation-settlement',
        label: 'Reconciliation & Settlement',
        routeKey: 'Reconciliation & Settlement',
        status: 'read_only_by_business_rule',
        description: 'Unapproved settlement rules (Decision required)',
        badge: 'Read-only',
      },
    ],
  },
  {
    id: 'company-accounting',
    label: 'Company Accounting',
    iconName: 'Folder',
    primaryRouteKey: 'Garage Revenue',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'garage-revenue',
        label: 'Garage Revenue',
        routeKey: 'Garage Revenue',
        status: 'implemented',
        description: 'Customer job charges & actual receipts',
      },
      {
        id: 'company-income',
        label: 'Company Income',
        routeKey: 'Company Income',
        status: 'implemented',
        description: 'Other company receipts & income sources',
      },
      {
        id: 'company-expenses',
        label: 'Company Expenses',
        routeKey: 'Company Expenses',
        status: 'implemented',
        description: 'Direct workshop & operating expenses',
      },
      {
        id: 'running-capital',
        label: 'Running Capital',
        routeKey: 'Running Capital',
        status: 'implemented',
        description: 'Vehicle-linked company capital contribution & recovery',
      },
      {
        id: 'company-result',
        label: 'Company Result',
        routeKey: 'Company Result',
        status: 'implemented',
        description: 'Provisional accounting components',
      },
      {
        id: 'transactions',
        label: 'Transactions',
        routeKey: 'Transactions',
        status: 'implemented',
        description: 'Company-wide source event register',
      },
      {
        id: 'owner-distribution',
        label: 'Owner Distribution',
        routeKey: 'Owner Distribution',
        status: 'read_only_by_business_rule',
        description: 'Owner allocation governance notice; business rules remain pending',
      },
      {
        id: 'audit-corrections',
        label: 'Audit & Corrections',
        routeKey: 'Audit & Corrections',
        status: 'implemented',
        description: 'Linked corrections & immutable action audit log',
      },
    ],
  },
  {
    id: 'reports',
    label: 'Reports',
    iconName: 'BarChart3',
    primaryRouteKey: 'All Reports',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'all-reports',
        label: 'All Reports',
        routeKey: 'All Reports',
        status: 'implemented',
        description: 'Complete directory of 17 operational reports',
      },
      {
        id: 'rep-consolidated',
        label: 'Company Consolidated',
        routeKey: 'Company Consolidated',
        status: 'implemented',
        description: 'Combined financial components',
      },
      {
        id: 'rep-garage-wise',
        label: 'Garage-wise',
        routeKey: 'Garage-wise',
        status: 'implemented',
        description: 'Attributed components by branch',
      },
      {
        id: 'rep-vehicle-cost',
        label: 'Vehicle Cost',
        routeKey: 'Vehicle Cost',
        status: 'implemented',
        description: 'Purchase, expense & stock issue ledger',
      },
      {
        id: 'rep-investor-fund',
        label: 'Investor Fund Report',
        routeKey: 'Investor Fund Report',
        status: 'implemented',
        description: 'Capital deployment & available reserve',
      },
      {
        id: 'rep-product-margin',
        label: 'Product Margin',
        routeKey: 'Product Margin',
        status: 'implemented',
        description: 'Batch issue margin & profit',
      },
      {
        id: 'rep-buyer-receivables',
        label: 'Buyer Receivables',
        routeKey: 'Buyer Receivables',
        status: 'implemented',
        description: 'Outstanding buyer payment balance',
      },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    iconName: 'Settings',
    primaryRouteKey: 'Appearance & Theme',
    status: 'implemented',
    dataSourceStatus: 'demo',
    children: [
      {
        id: 'theme-appearance',
        label: 'Appearance & Theme',
        routeKey: 'Appearance & Theme',
        status: 'implemented',
        description: 'Brand theme, color palette & visual styling',
      },
      {
        id: 'garages-branches',
        label: 'Garages / Branches',
        routeKey: 'Garages / Branches',
        status: 'implemented',
        description: 'Branch registry & active garage status',
      },
      {
        id: 'demo-data',
        label: 'Demo Data',
        routeKey: 'Demo Data',
        status: 'implemented',
        description: 'Snapshot import, refresh & seed reset',
      },
    ],
  },
];

const ROUTE_GROUP_ALIASES: Record<string, string> = {
  Overview: 'dashboard',
  'All Vehicles': 'vehicles',
  'Vehicle Detail': 'vehicles',
  'Garage Job Detail': 'garage-operations',
  Reports: 'reports',
  Accounting: 'company-accounting',
  Inventory: 'inventory',
  Settings: 'settings',
};

const FORM_ROUTE_KEYS: Record<string, string> = {
  vehicle: 'All Vehicles',
  job: 'Garage Jobs',
  jobWork: 'Garage Jobs',
  jobExpense: 'Garage Jobs',
  vehicleExpense: 'Garage Jobs',
  customerCharge: 'Garage Jobs',
  customerReceipt: 'Garage Jobs',
  purchase: 'Items & Purchases',
  issue: 'Items & Purchases',
  sale: 'Vehicle Sales',
  collection: 'Collections',
  saleCorrection: 'Sale Corrections & Refunds',
  refund: 'Sale Corrections & Refunds',
  fundCredit: 'Investor Fund',
  investor: 'Investor Fund',
  companyExpense: 'Company Expenses',
  otherIncome: 'Company Income',
  recovery: 'Investor Fund',
  capitalRecovery: 'Investor Fund',
  garage: 'Garages / Branches',
  garageEdit: 'Garages / Branches',
};

/**
 * Business routes default to Demo until a verified business API owns their
 * displayed records and mutations. Authentication/context APIs are outside
 * this navigation registry.
 */
export function getRouteDataSourceStatus(routeKey: string): DataSourceStatus {
  const group = navigationRegistry.find(
    (candidate) =>
      candidate.primaryRouteKey === routeKey ||
      candidate.children.some((child) => child.routeKey === routeKey)
  ) ?? navigationRegistry.find((candidate) => candidate.id === ROUTE_GROUP_ALIASES[routeKey]);

  if (!group) return 'demo';

  const child = group.children.find((candidate) => candidate.routeKey === routeKey);
  return child?.dataSourceStatus ?? group.dataSourceStatus;
}

/** Resolves a mutation form to its owning module for incremental backend integration. */
export function getFormDataSourceStatus(formType: string): DataSourceStatus {
  const routeKey = FORM_ROUTE_KEYS[formType];
  return routeKey ? getRouteDataSourceStatus(routeKey) : 'demo';
}
