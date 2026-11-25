import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AccountingEventRow } from '../../../api/accountingApi';
import type { GarageJob } from '../../../api/garageApi';
import { GarageRevenueView } from '../GarageRevenueView';

const ids = {
  user: '11111111-1111-4111-8111-111111111111',
  company: '22222222-2222-4222-8222-222222222222',
  branchA: '33333333-3333-4333-8333-333333333333',
  branchB: '44444444-4444-4444-8444-444444444444',
  vehicle1: '55555555-5555-4555-8555-555555555555',
  vehicle2: '66666666-6666-4666-8666-666666666666',
  jobExt: '77777777-7777-4777-8777-777777777777',
  jobStock: '88888888-8888-4888-8888-888888888888',
  event1: '99999999-9999-4999-8999-999999999999',
  event2: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
};

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useCompanyModuleStates: vi.fn(),
  useAccountingBranches: vi.fn(),
  useAccountingEvents: vi.fn(),
  garageJobs: vi.fn(),
  garageJob: vi.fn(),
}));

vi.mock('../../../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../../../api/queries', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../api/queries')>();
  return { ...actual, useCompanyModuleStates: mocks.useCompanyModuleStates };
});
vi.mock('../../../api/accountingQueries', () => ({
  useAccountingBranches: mocks.useAccountingBranches,
  useAccountingEvents: mocks.useAccountingEvents,
}));
vi.mock('../../../api/garageApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../api/garageApi')>();
  return {
    ...actual,
    garageApi: {
      ...actual.garageApi,
      jobs: mocks.garageJobs,
      job: mocks.garageJob,
    },
  };
});

const receiptRow: AccountingEventRow = {
  id: ids.event1,
  company_id: ids.company,
  branch_id: ids.branchA,
  branch_name: 'Main Branch',
  event_type: 'GARAGE_RECEIPT',
  amount: '300.00',
  currency: 'INR',
  category_id: null,
  category_name: null,
  description: 'Customer job receipt',
  source_reference: 'EXT-RCPT-01',
  effective_at: '2026-11-24T10:00:00Z',
  recorded_at: '2026-11-24T10:01:00Z',
  actor_id: ids.user,
  effect_sign: 1,
  reversal_of_id: null,
  replaces_event_id: null,
};

const reversalRow: AccountingEventRow = {
  ...receiptRow,
  id: ids.event2,
  branch_id: ids.branchB,
  branch_name: 'Second Branch',
  amount: '50.00',
  source_reference: 'EXT-RCPT-REV',
  effect_sign: -1,
  reversal_of_id: ids.event1,
};

const externalJobSummary: GarageJob = {
  id: ids.jobExt,
  vehicle_id: ids.vehicle1,
  branch_id: ids.branchA,
  vehicle_registration: 'P9-J04-CUST-01',
  vehicle_model: 'Swift',
  branch_name: 'Main Branch',
  context: 'EXTERNAL_CUSTOMER',
  contact_name: 'Ravi',
  contact_phone: '9999999999',
  status: 'OPEN',
  status_version: 1,
  created_at: '2026-11-24T09:00:00Z',
};

const externalJobDetail: GarageJob = {
  ...externalJobSummary,
  customer_charge: '500.00',
  charge_version: 1,
  received: '300.00',
  outstanding: '200.00',
  customer_cost_total: '180.00',
};

const stockJob: GarageJob = {
  ...externalJobDetail,
  id: ids.jobStock,
  vehicle_id: ids.vehicle2,
  branch_id: ids.branchB,
  vehicle_registration: 'P9-STOCK-01',
  context: 'STOCK',
  contact_name: '',
  contact_phone: '',
  customer_charge: null,
  received: '0.00',
  outstanding: null,
};

function renderView(onOpenGarageJobs = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  render(
    <QueryClientProvider client={client}>
      <GarageRevenueView onOpenGarageJobs={onOpenGarageJobs} />
    </QueryClientProvider>,
  );
  return { onOpenGarageJobs };
}

describe('GarageRevenueView', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({
      status: 'authenticated',
      user: {
        id: ids.user,
        login_id: 'acct-user',
        company_context_error: null,
        companies: [
          {
            id: ids.company,
            name: 'Test Company',
            slug: 'test-company',
            roles: ['accountant'],
            company_wide_roles: ['accountant'],
          },
        ],
      },
      currentCompany: {
        id: ids.company,
        name: 'Test Company',
        slug: 'test-company',
        roles: ['accountant'],
        company_wide_roles: ['accountant'],
      },
    });
    mocks.useCompanyModuleStates.mockReturnValue({
      isSuccess: true,
      data: {
        modules: [
          { code: 'garage', state: 'enabled' },
          { code: 'accounting', state: 'enabled' },
        ],
      },
    });
    mocks.useAccountingBranches.mockReturnValue({
      isSuccess: true,
      data: [
        { id: ids.branchA, tenant_id: ids.company, name: 'Main Branch' },
        { id: ids.branchB, tenant_id: ids.company, name: 'Second Branch' },
      ],
    });
    mocks.useAccountingEvents.mockReturnValue({
      isPending: false,
      isError: false,
      isSuccess: true,
      data: { count: 2, next: null, previous: null, results: [receiptRow, reversalRow] },
    });
    mocks.garageJobs.mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [externalJobSummary, stockJob],
    });
    mocks.garageJob.mockResolvedValue(externalJobDetail);
  });

  it('hydrates detail amounts and renders signed GARAGE_RECEIPT events separately from external customer charges and outstanding', async () => {
    renderView();

    expect(await screen.findByText('P9-J04-CUST-01')).toBeInTheDocument();
    expect(screen.queryByText('P9-STOCK-01')).not.toBeInTheDocument();
    expect(screen.getByText('EXT-RCPT-01')).toBeInTheDocument();
    expect(screen.getByText('Reversal')).toBeInTheDocument();
    expect(screen.getByText('₹250.00')).toBeInTheDocument();
    expect(await screen.findByLabelText('Customer Job Charges (Page): ₹500.00')).toBeInTheDocument();
    expect(await screen.findByLabelText('Outstanding Receivable (Page): ₹200.00')).toBeInTheDocument();
  });

  it('shows Unavailable instead of synthetic zero when the API errors', async () => {
    mocks.useAccountingEvents.mockReturnValue({
      isPending: false,
      isError: true,
      isSuccess: false,
      data: undefined,
    });

    renderView();

    expect(await screen.findByText('Actual Garage receipt events are unavailable right now.')).toBeInTheDocument();
    expect(await screen.findByLabelText('Actual Garage Receipts (Page): Unavailable')).toBeInTheDocument();
  });

  it('passes branch and EXTERNAL_CUSTOMER filters to backend before pagination and resets page', async () => {
    const user = userEvent.setup();
    renderView();

    await screen.findByText('P9-J04-CUST-01');
    expect(mocks.garageJobs).toHaveBeenCalledWith(ids.company, 1, expect.any(AbortSignal), {
      branchId: undefined,
      context: 'EXTERNAL_CUSTOMER',
    });
    await user.selectOptions(screen.getByLabelText('Filter by Branch'), ids.branchB);

    expect(mocks.useAccountingEvents).toHaveBeenLastCalledWith({
      page: 1,
      eventType: 'GARAGE_RECEIPT',
      branchId: ids.branchB,
      enabled: true,
    });
    expect(mocks.garageJobs).toHaveBeenLastCalledWith(ids.company, 1, expect.any(AbortSignal), {
      branchId: ids.branchB,
      context: 'EXTERNAL_CUSTOMER',
    });
    expect(screen.getByText('No external customer jobs found on this page.')).toBeInTheDocument();
  });
});
