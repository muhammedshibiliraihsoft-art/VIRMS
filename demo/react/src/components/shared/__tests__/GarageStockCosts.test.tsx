import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GarageStockCosts } from '../GarageStockCosts';
import { garageApi } from '../../../api/garageApi';
import { phase5Api } from '../../../api/phase5Api';

vi.mock('../../../api/garageApi', () => ({ garageApi: { stockCosts: vi.fn(), createStockCost: vi.fn(), linkStockCost: vi.fn() } }));
vi.mock('../../../api/phase5Api', () => ({ phase5Api: { expenses: vi.fn(), investors: vi.fn() } }));
const job = { id: 'job', vehicle_id: 'vehicle', branch_id: 'branch', status: 'OPEN', context: 'STOCK' };
beforeEach(() => { vi.resetAllMocks(); vi.mocked(garageApi.stockCosts).mockResolvedValue({ count: 0, previous: null, next: null, results: [] }); vi.mocked(phase5Api.expenses).mockResolvedValue({ count: 1, previous: null, next: null, running_capital_total: '50.00', results: [{ id: 'expense', description: 'Repair', amount: '50.00' }] } as never); });
const renderView = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><GarageStockCosts companyId="company" userId="user" job={job as never} canWrite canChooseInvestor={false} onBusyChange={() => {}} /></QueryClientProvider>);

describe('Stock job costs', () => {
  it('links an existing Vehicle Expense without creating another expense', async () => {
    vi.mocked(garageApi.linkStockCost).mockResolvedValue({ id: 'link' } as never);
    renderView();
    fireEvent.click(screen.getByRole('button', { name: 'Link existing expense' }));
    await screen.findByRole('option', { name: 'Repair · ₹50.00' });
    fireEvent.change(screen.getByLabelText('Vehicle expense'), { target: { value: 'expense' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(garageApi.linkStockCost).toHaveBeenCalledWith('company', 'user', 'job', 'expense'));
    expect(garageApi.createStockCost).not.toHaveBeenCalled();
  });
  it('retains the new cost if the backend rejects it', async () => {
    vi.mocked(garageApi.createStockCost).mockRejectedValue(new Error('Investor required'));
    renderView();
    fireEvent.click(screen.getByRole('button', { name: 'Add vehicle cost' }));
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '100' } });
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'Repair' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Investor required');
    expect(screen.getByLabelText('Description')).toHaveValue('Repair');
  });
});
