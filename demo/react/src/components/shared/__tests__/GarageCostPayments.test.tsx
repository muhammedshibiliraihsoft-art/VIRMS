import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GarageCostPayments } from '../GarageCostPayments';
import { garageApi } from '../../../api/garageApi';
import { accountingAccounts, accountingCategories } from '../../../api/accountingApi';

vi.mock('../../../api/garageApi', () => ({ garageApi: { customerCostPayments: vi.fn(), customerCostRefunds: vi.fn(), payCustomerCost: vi.fn(), refundCustomerCost: vi.fn(), customerCostRefundPreview: vi.fn() } }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: vi.fn(), accountingCategories: vi.fn() }));
const cost = { id: 'cost', actor_id: 'actor', description: 'Parts', version: 0, amount: '100.00', paid: '20.00', refunded: '0.00', payable: '80.00', created_at: '2026-11-17T00:00:00Z' };
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(garageApi.customerCostPayments).mockResolvedValue({ count: 0, previous: null, next: null, results: [] });
  vi.mocked(garageApi.customerCostRefunds).mockResolvedValue({ count: 0, previous: null, next: null, results: [] });
  vi.mocked(accountingAccounts).mockResolvedValue([{ id: 'account', label: 'Cash', account_type: 'CASH', is_active: true }]);
  vi.mocked(accountingCategories).mockResolvedValue([]);
});
const renderPanel = (canWrite = true, accountingEnabled = true) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><GarageCostPayments companyId="company" userId="user" jobId="job" cost={cost} canWrite={canWrite} accountingEnabled={accountingEnabled} disabled={false} onBusyChange={() => {}} onClose={() => {}} /></QueryClientProvider>);

describe('Garage cost payments', () => {
  it('shows the refund preview without posting until the accountant saves it', async () => {
    vi.mocked(garageApi.customerCostRefundPreview).mockResolvedValue({ paid: '20.00', previous_refunds: '0.00', applied_amount: '20.00', excess_amount: '10.00' });
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Record actual refund' }));
    fireEvent.change(screen.getByLabelText('Actual refund amount'), { target: { value: '30' } });
    expect(garageApi.customerCostRefundPreview).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Calculate refund split' }));
    expect(await screen.findByText('Applied to Job cost ₹20.00 · Remaining for another record ₹10.00. Posting rechecks these amounts.')).toBeInTheDocument();
    expect(screen.getByText(/preview only; no cash or accounting entry/)).toBeInTheDocument();
    expect(garageApi.refundCustomerCost).not.toHaveBeenCalled();
  });
  it('recalculates the same amount and hides stale results while loading', async () => {
    let finish!: (value: { paid: string; previous_refunds: string; applied_amount: string; excess_amount: string }) => void;
    vi.mocked(garageApi.customerCostRefundPreview).mockResolvedValueOnce({ paid: '20.00', previous_refunds: '0.00', applied_amount: '20.00', excess_amount: '10.00' }).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Record actual refund' }));
    fireEvent.change(screen.getByLabelText('Actual refund amount'), { target: { value: '30' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculate refund split' }));
    expect(await screen.findByText(/Applied to Job cost ₹20.00 · Remaining for another record ₹10.00/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Calculate refund split' }));
    await waitFor(() => expect(garageApi.customerCostRefundPreview).toHaveBeenCalledTimes(2));
    expect(screen.queryByText(/Applied to Job cost ₹20.00 · Remaining for another record ₹10.00/)).not.toBeInTheDocument();
    finish({ paid: '25.00', previous_refunds: '0.00', applied_amount: '25.00', excess_amount: '5.00' });
    expect(await screen.findByText(/Applied to Job cost ₹25.00 · Remaining for another record ₹5.00/)).toBeInTheDocument();
  });
  it('requires an explicit Income category and note for excess, then posts the actual refund', async () => {
    vi.mocked(garageApi.customerCostRefundPreview).mockResolvedValue({ paid: '20.00', previous_refunds: '0.00', applied_amount: '20.00', excess_amount: '10.00' });
    vi.mocked(accountingCategories).mockResolvedValue([{ id: 'income-category', kind: 'INCOME', label: 'Other income', is_active: true }, { id: 'expense-category', kind: 'EXPENSE', label: 'Expense', is_active: true }]);
    vi.mocked(garageApi.refundCustomerCost).mockResolvedValue({ id: 'refund' } as never);
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Record actual refund' }));
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Cash / Bank account receiving the refund'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Actual refund amount'), { target: { value: '30' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculate refund split' }));
    await screen.findByRole('option', { name: 'Other income' });
    const save = screen.getByRole('button', { name: 'Save actual refund' });
    expect(save).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Income category for excess amount'), { target: { value: 'income-category' } });
    fireEvent.change(screen.getByLabelText('Why is the excess Company Income?'), { target: { value: 'Workshop returned more than the paid amount' } });
    expect(save).toBeEnabled();
    fireEvent.click(save);
    await waitFor(() => expect(garageApi.refundCustomerCost).toHaveBeenCalledWith('company', 'user', 'job', 'cost', {
      account_id: 'account', amount: '30', excess_income_category_id: 'income-category', excess_income_description: 'Workshop returned more than the paid amount',
    }));
    await waitFor(() => expect(screen.queryByLabelText('Actual refund amount')).not.toBeInTheDocument());
  });
  it('keeps the refund form visible after a failed save', async () => {
    vi.mocked(garageApi.customerCostRefundPreview).mockResolvedValue({ paid: '20.00', previous_refunds: '0.00', applied_amount: '20.00', excess_amount: '0.00' });
    vi.mocked(garageApi.refundCustomerCost).mockRejectedValue(new Error('Refund could not be saved.'));
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Record actual refund' }));
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Cash / Bank account receiving the refund'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Actual refund amount'), { target: { value: '10' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculate refund split' }));
    await screen.findByText(/Applied to Job cost/);
    fireEvent.click(screen.getByRole('button', { name: 'Save actual refund' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Refund could not be saved');
    expect(screen.getByLabelText('Actual refund amount')).toHaveValue(10);
  });
  it('posts a confirmed actual payment and refreshes only after success', async () => {
    vi.mocked(garageApi.payCustomerCost).mockResolvedValue({ id: 'payment' } as never);
    renderPanel();
    expect(await screen.findByText(/Paid ₹20.00 · Refunded ₹0.00 · Due ₹80.00/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Record cost payment' }));
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Cash / Bank account'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '30' } });
    expect(garageApi.payCustomerCost).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Save payment' }));
    await waitFor(() => expect(garageApi.payCustomerCost).toHaveBeenCalledWith('company', 'user', 'job', 'cost', { account_id: 'account', amount: '30' }));
    await waitFor(() => expect(screen.queryByLabelText('Amount')).not.toBeInTheDocument());
  });
  it('keeps an unsuccessful payment visible for review', async () => {
    vi.mocked(garageApi.payCustomerCost).mockRejectedValue(new Error('Payment exceeds the remaining cost amount.'));
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Record cost payment' }));
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Cash / Bank account'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '90' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save payment' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('exceeds');
    expect(screen.getByLabelText('Amount')).toHaveValue(90);
  });
  it('does not offer a payment when Accounting is off or the viewer cannot write', () => {
    const view = renderPanel(true, false);
    expect(screen.queryByRole('button', { name: 'Record cost payment' })).not.toBeInTheDocument();
    view.unmount();
    renderPanel(false, true);
    expect(screen.queryByRole('button', { name: 'Record cost payment' })).not.toBeInTheDocument();
  });
});
