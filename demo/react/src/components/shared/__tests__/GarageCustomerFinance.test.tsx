import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GarageCustomerFinance } from '../GarageCustomerFinance';
import { garageApi } from '../../../api/garageApi';
import { accountingAccounts } from '../../../api/accountingApi';

vi.mock('../../../api/garageApi', () => ({ garageApi: { charge: vi.fn(), customerCost: vi.fn(), customerCosts: vi.fn(), correctCustomerCost: vi.fn(), receipt: vi.fn() } }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: vi.fn() }));
const job = { id: 'job', context: 'EXTERNAL_CUSTOMER', status: 'OPEN', charge_version: 1, customer_charge: '100.00', customer_cost_total: '10.00', outstanding: '80.00' };
beforeEach(() => { vi.resetAllMocks(); vi.mocked(accountingAccounts).mockResolvedValue([{ id: 'account', label: 'Cash', account_type: 'CASH', is_active: true }]); vi.mocked(garageApi.customerCosts).mockResolvedValue({ count: 0, previous: null, next: null, results: [] }); });
const renderForm = (accountingEnabled = true) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><GarageCustomerFinance companyId="company" userId="user" job={job as never} accountingEnabled={accountingEnabled} /></QueryClientProvider>);

describe('Garage customer amounts', () => {
  it('explains that recorded costs do not automatically change the agreed charge', () => {
    renderForm();
    expect(screen.getByText('Recorded costs do not automatically change the customer charge.')).toBeInTheDocument();
  });
  it('does not submit a charge correction using a version refreshed after the form opened', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
    const view = (row: typeof job) => <QueryClientProvider client={client}><GarageCustomerFinance companyId="company" userId="user" job={row as never} accountingEnabled /></QueryClientProvider>;
    const { rerender } = render(view(job));
    fireEvent.click(screen.getByRole('button', { name: 'Correct charge' }));
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '90' } });
    fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Correction' } });
    rerender(view({ ...job, charge_version: 2, customer_charge: '120.00' }));
    expect(screen.getByRole('alert')).toHaveTextContent('changed');
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    expect(garageApi.charge).not.toHaveBeenCalled();
  });
  it('records a receipt with its account and reference only after submission', async () => {
    vi.mocked(garageApi.receipt).mockResolvedValue({ id: 'receipt' } as never);
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: 'Record receipt' }));
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '40.00' } });
    const account = await screen.findByLabelText('Cash / Bank account');
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(account, { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Receipt reference'), { target: { value: 'ref-1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(garageApi.receipt).toHaveBeenCalledWith('company', 'user', 'job', { amount: '40.00', account_id: 'account', reference: 'ref-1' }));
    await waitFor(() => expect(screen.queryByLabelText('Receipt reference')).not.toBeInTheDocument());
  });
  it('passes an explicitly selected receipt date to the backend', async () => {
    vi.mocked(garageApi.receipt).mockResolvedValue({ id: 'receipt' } as never);
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: 'Record receipt' }));
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '40' } });
    fireEvent.change(screen.getByLabelText('Cash / Bank account'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Receipt reference'), { target: { value: 'ref-2' } });
    fireEvent.change(screen.getByLabelText('Received date and time (optional)'), { target: { value: '2026-10-01T10:30' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(garageApi.receipt).toHaveBeenCalledWith('company', 'user', 'job', { amount: '40', account_id: 'account', reference: 'ref-2', effective_at: new Date('2026-10-01T10:30').toISOString() }));
  });
  it('retains a failed charge correction and does not show receipt when Accounting is off', async () => {
    vi.mocked(garageApi.charge).mockRejectedValue(new Error('Conflict'));
    renderForm(false);
    expect(screen.queryByRole('button', { name: 'Record receipt' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Correct charge' }));
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '90' } });
    fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Correction' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Conflict');
    expect(screen.getByLabelText('Amount')).toHaveValue(90);
    expect(garageApi.charge).toHaveBeenCalledWith('company', 'user', 'job', { amount: '90', expected_version: 1, reason: 'Correction' });
  });
  it('submits a cost correction with the displayed version and a reason', async () => {
    const cost = { id: 'cost', description: 'Parts', amount: '50.00', version: 2 };
    vi.mocked(garageApi.customerCosts).mockResolvedValue({ count: 1, previous: null, next: null, results: [cost] } as never);
    vi.mocked(garageApi.correctCustomerCost).mockResolvedValue({ ...cost, amount: '40.00', version: 3 } as never);
    renderForm();
    fireEvent.click(await screen.findByRole('button', { name: 'Correct' }));
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '40' } });
    fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Invoice correction' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(garageApi.correctCustomerCost).toHaveBeenCalledWith('company', 'user', 'job', 'cost', { amount: '40', expected_version: 2, reason: 'Invoice correction' }));
  });
});
