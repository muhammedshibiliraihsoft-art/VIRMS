import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AllVehiclesView } from '../AllVehiclesView';
import { phase5Api } from '../../api/phase5Api';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useCompanyModuleStates: vi.fn(),
  canWrite: vi.fn(),
  vehicleRegister: vi.fn(),
}));

vi.mock('../../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../../api/queries', () => ({
  hasCompanyBranchReadRole: () => true,
  useCompanyModuleStates: mocks.useCompanyModuleStates,
}));
vi.mock('../../api/phase5Api', () => ({ phase5Api: { vehicleRegister: mocks.vehicleRegister } }));
vi.mock('../../auth/RolePresentationContext', () => ({ useCanPresentBusinessWriteActions: mocks.canWrite }));

const ids = {
  user: '11111111-1111-4111-8111-111111111111',
  company: '22222222-2222-4222-8222-222222222222',
  branch: '33333333-3333-4333-8333-333333333333',
  vehicle: '44444444-4444-4444-8444-444444444444',
};

const vehicle = {
  id: ids.vehicle,
  company_id: ids.company,
  branch_id: ids.branch,
  branch_name: 'West Branch',
  registration: 'KL 11 API 9001',
  model: 'Jeep Wrangler',
  is_active: true,
  is_sold: false,
  sale_id: null,
  contexts: ['STOCK'],
  type: 'Stock / Investor',
  person: 'North Motors',
  person_label: 'Seller',
  status: 'PURCHASED',
  purchase_cost: '9000.00',
  total_cost: '9500.00',
  financial_available: true,
  customer_job_count: 0,
  customer_contact: null,
  customer_status: null,
} as const;

const summary = {
  total: 1,
  stock_count: 1,
  customer_count: 0,
  stock_total_cost: '9500.00',
  in_work: 0,
  sold: 0,
  purchased: 1,
  customer_jobs: 0,
  open_customer_jobs: 0,
  completed_customer_jobs: 0,
  stock_in_work: 0,
  stock_purchased: 1,
  stock_sold: 0,
};

function response(page = 1, count = 1) {
  return {
    company_id: ids.company,
    branch_id: null,
    count,
    next: page === 1 && count > 20 ? 'page=2' : null,
    previous: page > 1 ? 'page=1' : null,
    results: count === 0 ? [] : page === 1 ? [vehicle] : [{ ...vehicle, id: '55555555-5555-4555-8555-555555555555', registration: 'KL 11 API 9002' }],
    summary: { ...summary, total: count },
  };
}

function renderView(mode: 'all' | 'customer' = 'all') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AllVehiclesView
        mode={mode}
        onRegisterVehicle={vi.fn()}
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.canWrite.mockReturnValue(false);
  mocks.useAuth.mockReturnValue({
    status: 'authenticated',
    user: { id: ids.user, companies: [{ id: ids.company, roles: ['accountant'] }] },
    currentCompany: { id: ids.company, company_wide_roles: ['accountant'], roles: ['accountant'] },
  });
  mocks.useCompanyModuleStates.mockReturnValue({
    isLoading: false,
    isSuccess: true,
    isError: false,
    data: { modules: [{ code: 'vehicle_management', state: 'enabled' }] },
  });
  vi.mocked(phase5Api.vehicleRegister).mockResolvedValue(response() as never);
});

describe('AllVehiclesView live Vehicle register', () => {
  it('renders authorized API values and keeps money strings exact instead of showing prototype rows', async () => {
    renderView();

    expect(await screen.findByText('KL 11 API 9001')).toBeInTheDocument();
    expect(screen.getByText('West Branch')).toBeInTheDocument();
    expect(screen.getByText('₹9,500.00')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Page key metrics' })).toHaveTextContent('Total Vehicles');
    expect(screen.getByRole('region', { name: 'Page key metrics' })).toHaveTextContent('1');
    expect(screen.queryByText('KL 11 AB 4821')).not.toBeInTheDocument();
    expect(phase5Api.vehicleRegister).toHaveBeenCalledWith(ids.company, {
      page: 1, search: undefined, context: 'all', status: 'all',
    }, expect.any(AbortSignal));
  });

  it('uses server pagination controls and requests the next page', async () => {
    vi.mocked(phase5Api.vehicleRegister)
      .mockResolvedValueOnce(response(1, 21) as never)
      .mockResolvedValueOnce(response(2, 21) as never);
    renderView();

    fireEvent.click(await screen.findByRole('button', { name: 'Next' }));

    expect(await screen.findByText('KL 11 API 9002')).toBeInTheDocument();
    await waitFor(() => expect(phase5Api.vehicleRegister).toHaveBeenLastCalledWith(ids.company, {
      page: 2, search: undefined, context: 'all', status: 'all',
    }, expect.any(AbortSignal)));
  });

  it('sends category changes to the API and uses customer-job KPIs on the Customer view', async () => {
    vi.mocked(phase5Api.vehicleRegister).mockResolvedValueOnce({
      ...response(),
      results: [],
      summary: { ...summary, total: 1, customer_count: 1, customer_jobs: 2, open_customer_jobs: 1, completed_customer_jobs: 1 },
    } as never);
    renderView('customer');

    const metrics = screen.getByRole('region', { name: 'Page key metrics' });
    expect(await screen.findByText('No vehicles found')).toBeInTheDocument();
    expect(metrics).toHaveTextContent('Customer Vehicles');
    expect(metrics).toHaveTextContent('Open Customer Jobs');
    expect(metrics).toHaveTextContent('Completed Customer Jobs');
    await waitFor(() => expect(phase5Api.vehicleRegister).toHaveBeenCalledWith(ids.company, {
      page: 1, search: undefined, context: 'customer', status: 'all',
    }, expect.any(AbortSignal)));
  });

  it('shows zero only for a successful empty API response', async () => {
    vi.mocked(phase5Api.vehicleRegister).mockResolvedValueOnce(response(1, 0) as never);
    renderView();

    expect(await screen.findByText('No vehicles found')).toBeInTheDocument();
    const metrics = screen.getByRole('region', { name: 'Page key metrics' });
    expect(metrics).toHaveTextContent('0');
    expect(metrics).not.toHaveTextContent('Unavailable');
  });

  it('does not turn an API failure into zero-valued live KPIs', async () => {
    vi.mocked(phase5Api.vehicleRegister).mockRejectedValueOnce(new Error('Forbidden'));
    renderView();

    expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded');
    expect(screen.getByRole('region', { name: 'Page key metrics' })).toHaveTextContent('Unavailable');
    expect(screen.getByRole('region', { name: 'Page key metrics' })).not.toHaveTextContent('₹0.00');
  });
});
