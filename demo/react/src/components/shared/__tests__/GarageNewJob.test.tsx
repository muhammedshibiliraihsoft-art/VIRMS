import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GarageNewJob } from '../GarageNewJob';
import { garageApi } from '../../../api/garageApi';
import { phase5Api } from '../../../api/phase5Api';

vi.mock('../../../api/garageApi', () => ({ garageApi: { createJob: vi.fn() } }));
vi.mock('../../../api/phase5Api', () => ({ phase5Api: { vehicles: vi.fn() } }));
const vehicle = { id: 'vehicle', branch_id: 'branch', branch_name: 'Central', registration: 'KL01AB1234', model: 'Car' };
const created = vi.fn();
beforeEach(() => { vi.resetAllMocks(); vi.mocked(phase5Api.vehicles).mockResolvedValue({ count: 1, previous: null, next: null, results: [vehicle] } as never); });
const renderForm = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><GarageNewJob companyId="company" userId="user" onCreated={created} onClose={() => {}} /></QueryClientProvider>);

describe('Garage job creation', () => {
  it('saves the selected vehicle and required customer name with optional phone', async () => {
    vi.mocked(garageApi.createJob).mockResolvedValue({ id: 'new-job' } as never);
    renderForm();
    const select = await screen.findByLabelText('Vehicle');
    fireEvent.change(select, { target: { value: 'vehicle' } });
    fireEvent.change(screen.getByLabelText('Job type'), { target: { value: 'EXTERNAL_CUSTOMER' } });
    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: ' Alex ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save job' }));
    expect(await screen.findByLabelText('New Garage Job')).toBeInTheDocument();
    await vi.waitFor(() => expect(created).toHaveBeenCalledWith({ id: 'new-job' }));
    expect(garageApi.createJob).toHaveBeenCalledWith('company', 'user', { vehicle_id: 'vehicle', branch_id: 'branch', context: 'EXTERNAL_CUSTOMER', contact_name: 'Alex', contact_phone: '' });
  });

  it('leaves the form and selection available when saving fails', async () => {
    vi.mocked(garageApi.createJob).mockRejectedValue(new Error('Save failed'));
    renderForm();
    fireEvent.change(await screen.findByLabelText('Vehicle'), { target: { value: 'vehicle' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save job' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Save failed');
    expect(created).not.toHaveBeenCalled();
    expect(screen.getByText(/Selected:/)).toHaveTextContent('KL01AB1234');
  });
});
