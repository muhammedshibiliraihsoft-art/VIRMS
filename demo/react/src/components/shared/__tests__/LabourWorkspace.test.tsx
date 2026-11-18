import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LabourWorkspace } from '../LabourWorkspace';
import { garageApi } from '../../../api/garageApi';
import { accountingAccounts } from '../../../api/accountingApi';

vi.mock('../../../auth/AuthContext', () => ({ useAuth: () => ({ status: 'authenticated', user: { id: 'user' }, currentCompany: { id: 'company', roles: ['accountant'] } }) }));
vi.mock('../../../api/queries', () => ({ hasCompanyBranchReadRole: () => true, useCompanyModuleStates: () => ({ isSuccess: true, data: { modules: [{ code: 'labour', state: 'enabled' }, { code: 'accounting', state: 'enabled' }] } }) }));
vi.mock('../../../api/authApi', () => ({ authApi: { branches: vi.fn().mockResolvedValue({ previous: null, next: null, results: [{ id: 'branch', name: 'Central' }] }) } }));
vi.mock('../../../api/garageApi', () => ({ garageApi: { people: vi.fn(), payments: vi.fn(), createPerson: vi.fn(), updatePerson: vi.fn(), setPersonStatus: vi.fn(), payPerson: vi.fn() } }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: vi.fn() }));

const person = { id: 'person', branch_id: 'branch', branch_name: 'Central', name: 'Worker', phone: '', is_active: true, status_version: 0, updated_at: '2026-11-17T00:00:00Z' };
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(garageApi.people).mockResolvedValue({ count: 1, previous: null, next: null, results: [person] } as never);
  vi.mocked(garageApi.payments).mockResolvedValue({ count: 0, previous: null, next: null, results: [] });
  vi.mocked(accountingAccounts).mockResolvedValue([{ id: 'account', label: 'Cash', account_type: 'CASH', is_active: true }]);
});
const renderView = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><LabourWorkspace /></QueryClientProvider>);

describe('Labour workspace', () => {
  it('does not save an open edit using a newer status update timestamp', async () => {
    vi.mocked(garageApi.setPersonStatus).mockResolvedValue({ ...person, is_active: false, status_version: 1, updated_at: '2026-11-18T00:00:00Z' } as never);
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /Worker/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Edit details' }));
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Edited worker' } });
    fireEvent.click(screen.getByRole('button', { name: 'Deactivate' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('changed');
    expect(screen.getByRole('button', { name: 'Save details' })).toBeDisabled();
    expect(garageApi.updatePerson).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Edit details' }));
    expect(screen.getByLabelText('Name')).toHaveValue('Worker');
    expect(screen.getByRole('button', { name: 'Save details' })).toBeEnabled();
  });
  it('loads an assigned worker and payment history', async () => {
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /Worker/ }));
    expect(await screen.findByText('No payments recorded.')).toBeInTheDocument();
    expect(garageApi.payments).toHaveBeenCalledWith('company', 'person', 1, expect.any(AbortSignal));
  });
  it('records a payment only after an account and amount are provided', async () => {
    vi.mocked(garageApi.payPerson).mockResolvedValue({ id: 'payment' } as never);
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /Worker/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Record payment' }));
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Cash / Bank account'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '200' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Record payment' })[1]);
    await waitFor(() => expect(garageApi.payPerson).toHaveBeenCalledWith('company', 'user', 'person', expect.objectContaining({ account_id: 'account', amount: '200', effective_at: expect.any(String) })));
  });
  it('keeps entered worker data when creation fails', async () => {
    vi.mocked(garageApi.createPerson).mockRejectedValue(new Error('Save failed'));
    renderView();
    fireEvent.click(screen.getByRole('button', { name: 'Add person' }));
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'New worker' } });
    await screen.findByRole('option', { name: 'Central' });
    fireEvent.change(screen.getByLabelText('Branch'), { target: { value: 'branch' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Save failed');
    expect(screen.getByLabelText('Name')).toHaveValue('New worker');
  });
  it('edits details using the last observed timestamp', async () => {
    vi.mocked(garageApi.updatePerson).mockResolvedValue({ ...person, name: 'Corrected' } as never);
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /Worker/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Edit details' }));
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Corrected' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
    await waitFor(() => expect(garageApi.updatePerson).toHaveBeenCalledWith('company', 'user', 'person', { name: 'Corrected', phone: '', expected_updated_at: person.updated_at }));
  });
});
