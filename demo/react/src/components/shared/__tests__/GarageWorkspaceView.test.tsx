import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { GarageWorkspaceView } from '../GarageWorkspaceView';
import { garageApi } from '../../../api/garageApi';

vi.mock('../../../auth/AuthContext', () => ({ useAuth: () => ({ status: 'authenticated', user: { id: 'user' }, currentCompany: { id: 'company', roles: ['accountant'], company_wide_roles: [] } }) }));
vi.mock('../../../api/queries', () => ({ hasCompanyBranchReadRole: () => true, useCompanyModuleStates: () => ({ isSuccess: true, data: { modules: [{ code: 'garage', state: 'enabled' }] } }) }));
vi.mock('../../../api/garageApi', () => ({ garageApi: { jobs: vi.fn(), job: vi.fn(), work: vi.fn(), customerCosts: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }), stockCosts: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }), addWork: vi.fn(), setStatus: vi.fn() } }));

const row = { id: 'job', vehicle_registration: 'KL01AB1234', vehicle_model: 'Car', branch_name: 'Central', context: 'STOCK', status: 'OPEN' };
const renderView = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><GarageWorkspaceView /></QueryClientProvider>);

describe('Garage workspace', () => {
  it('loads Company jobs and the selected Job work history', async () => {
    vi.mocked(garageApi.jobs).mockResolvedValue({ count: 1, next: null, previous: null, results: [row] } as never);
    vi.mocked(garageApi.job).mockResolvedValue(row as never);
    vi.mocked(garageApi.work).mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 'work', description: 'Brake repair' }] } as never);
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /KL01AB1234/ }));
    expect(await screen.findByText('Brake repair')).toBeInTheDocument();
    expect(garageApi.job).toHaveBeenCalledWith('company', 'job', expect.any(AbortSignal));
  });

  it('keeps status and Customer finance component keys distinct for an external Job', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    const externalRow = { ...row, context: 'EXTERNAL_CUSTOMER', contact_name: 'Customer' };
    vi.mocked(garageApi.jobs).mockResolvedValue({ count: 1, next: null, previous: null, results: [externalRow] } as never);
    vi.mocked(garageApi.job).mockResolvedValue(externalRow as never);
    vi.mocked(garageApi.work).mockResolvedValue({ count: 0, next: null, previous: null, results: [] } as never);
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /KL01AB1234/ }));
    expect(await screen.findByText('Customer job amounts')).toBeInTheDocument();
    expect(consoleError.mock.calls.flat().join(' ')).not.toContain('same key');
  });

  it('shows a load failure instead of sample jobs', async () => {
    vi.mocked(garageApi.jobs).mockRejectedValue(new Error('Unavailable'));
    renderView();
    expect(await screen.findByRole('alert')).toHaveTextContent('Jobs could not be loaded');
    expect(screen.queryByText('KL01AB1234')).not.toBeInTheDocument();
  });

  it('keeps a failed work entry visible and reports the error', async () => {
    vi.mocked(garageApi.jobs).mockResolvedValue({ count: 1, next: null, previous: null, results: [row] } as never);
    vi.mocked(garageApi.job).mockResolvedValue(row as never);
    vi.mocked(garageApi.work).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
    vi.mocked(garageApi.addWork).mockRejectedValue(new Error('Save failed'));
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /KL01AB1234/ }));
    const field = await screen.findByLabelText('Work description');
    fireEvent.change(field, { target: { value: 'Brake repair' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add work' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Save failed');
    expect(field).toHaveValue('Brake repair');
  });
});
