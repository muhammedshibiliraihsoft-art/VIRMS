export interface BranchSummary {
  id: string;
  name: string;
  roles: string[];
}

export interface CompanySummary {
  id: string;
  name: string;
  roles: string[];
  company_wide_roles: string[];
  branches_truncated: boolean;
  branches: BranchSummary[];
}

export interface AuthMe {
  id: string;
  login_id: string;
  must_change_password: boolean;
  roles: string[];
  tenant_ids: string[];
  companies: CompanySummary[];
  company_context_truncated: boolean;
}

export interface LoginResponse {
  must_change_password: boolean;
}

export interface BranchPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: BranchListItem[];
}

export interface BranchListItem {
  id: string;
  tenant_id: string;
  name: string;
}

export const COMPANY_MODULE_CODES = [
  'accounting',
  'investment',
  'garage',
  'investor_portal',
  'vehicle_management',
  'vehicle_expense_management',
  'sales_receivables',
  'media_vehicle_publication',
  'public_vehicle_access',
  'labour',
  'reports_dashboard',
  'audit_corrections',
  'gst_tax_invoice',
  'owner_ai_assistant',
] as const;

export type CompanyModuleCode = (typeof COMPANY_MODULE_CODES)[number];
export type CompanyModuleAvailability = 'unconfigured' | 'enabled' | 'disabled';

export interface CompanyModuleStateRow {
  code: CompanyModuleCode;
  state: CompanyModuleAvailability;
  version: number | null;
  effective_from: string | null;
}

export interface CompanyModuleStatesResponse {
  company_id: string;
  modules: CompanyModuleStateRow[];
}

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

const isoDateTimePattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

function isCompanyModuleStateRow(value: unknown, index: number): value is CompanyModuleStateRow {
  if (!value || typeof value !== 'object') return false;
  const row = value as Record<string, unknown>;
  if (row.code !== COMPANY_MODULE_CODES[index]) return false;

  if (row.state === 'unconfigured') {
    return row.version === null && row.effective_from === null;
  }

  return (
    (row.state === 'enabled' || row.state === 'disabled') &&
    typeof row.version === 'number' &&
    Number.isInteger(row.version) &&
    row.version >= 1 &&
    typeof row.effective_from === 'string' &&
    isoDateTimePattern.test(row.effective_from) &&
    Number.isFinite(Date.parse(row.effective_from))
  );
}

export function parseCompanyModuleStates(value: unknown): CompanyModuleStatesResponse {
  if (!value || typeof value !== 'object') {
    throw new Error('Invalid Company module-state response.');
  }
  const row = value as Record<string, unknown>;
  if (
    typeof row.company_id !== 'string' ||
    !uuidPattern.test(row.company_id) ||
    !Array.isArray(row.modules) ||
    row.modules.length !== COMPANY_MODULE_CODES.length ||
    !row.modules.every(isCompanyModuleStateRow)
  ) {
    throw new Error('Invalid Company module-state response.');
  }
  return row as unknown as CompanyModuleStatesResponse;
}

function isBranch(value: unknown): value is BranchSummary {
  if (!value || typeof value !== 'object') return false;
  const row = value as Record<string, unknown>;
  return isString(row.id) && uuidPattern.test(row.id) && isString(row.name) && isStringArray(row.roles);
}

function isBranchListItem(value: unknown): value is BranchListItem {
  if (!value || typeof value !== 'object') return false;
  const row = value as Record<string, unknown>;
  return (
    isString(row.id) &&
    uuidPattern.test(row.id) &&
    isString(row.tenant_id) &&
    uuidPattern.test(row.tenant_id) &&
    isString(row.name)
  );
}

function isCompany(value: unknown): value is CompanySummary {
  if (!value || typeof value !== 'object') return false;
  const row = value as Record<string, unknown>;
  return (
    isString(row.id) &&
    uuidPattern.test(row.id) &&
    isString(row.name) &&
    isStringArray(row.roles) &&
    isStringArray(row.company_wide_roles) &&
    typeof row.branches_truncated === 'boolean' &&
    Array.isArray(row.branches) &&
    row.branches.every(isBranch)
  );
}

export function parseAuthMe(value: unknown): AuthMe {
  if (!value || typeof value !== 'object') throw new Error('Invalid /auth/me response.');
  const row = value as Record<string, unknown>;
  if (
    !isString(row.id) ||
    !uuidPattern.test(row.id) ||
    !isString(row.login_id) ||
    typeof row.must_change_password !== 'boolean' ||
    !isStringArray(row.roles) ||
    !Array.isArray(row.tenant_ids) ||
    !row.tenant_ids.every((id) => isString(id) && uuidPattern.test(id)) ||
    !Array.isArray(row.companies) ||
    !row.companies.every(isCompany) ||
    typeof row.company_context_truncated !== 'boolean'
  ) {
    throw new Error('Invalid /auth/me response.');
  }
  return row as unknown as AuthMe;
}

export function parseBranchPage(value: unknown): BranchPage {
  if (!value || typeof value !== 'object') throw new Error('Invalid Branch response.');
  const row = value as Record<string, unknown>;
  if (
    typeof row.count !== 'number' ||
    !(row.next === null || isString(row.next)) ||
    !(row.previous === null || isString(row.previous)) ||
    !Array.isArray(row.results) ||
    !row.results.every(isBranchListItem)
  ) {
    throw new Error('Invalid Branch response.');
  }
  return row as unknown as BranchPage;
}
