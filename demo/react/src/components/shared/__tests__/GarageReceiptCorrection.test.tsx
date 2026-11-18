import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GarageReceiptCorrection } from '../GarageReceiptCorrection';
import { garageApi } from '../../../api/garageApi';
import { accountingAccounts } from '../../../api/accountingApi';

vi.mock('../../../api/garageApi', () => ({ garageApi: { receiptCorrectionHistory: vi.fn(), correctReceipt: vi.fn() } }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: vi.fn() }));
const receipt = { id: 'receipt', event_id: 'event', actor_id: 'actor', amount: '40.00', reference: 'R1', effective_at: '2026-10-01T05:00:30.123456Z' };
beforeEach(() => { vi.resetAllMocks(); vi.mocked(accountingAccounts).mockResolvedValue([{ id: 'account', label: 'Cash', account_type: 'CASH', is_active: true }]); });
const renderForm = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><GarageReceiptCorrection companyId="company" userId="user" jobId="job" receipt={receipt} canCorrect onBusyChange={() => {}} /></QueryClientProvider>);

describe('Garage receipt correction', () => {
  it('blocks a form when a refreshed receipt has changed since it was opened', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
    const renderReceipt = (row: typeof receipt) => <QueryClientProvider client={client}><GarageReceiptCorrection companyId="company" userId="user" jobId="job" receipt={row} canCorrect onBusyChange={() => {}} /></QueryClientProvider>;
    const { rerender } = render(renderReceipt(receipt));
    fireEvent.click(screen.getByRole('button', { name: 'Correct receipt' }));
    fireEvent.change(screen.getByLabelText('What happened?'), { target: { value: 'REVERSE_ONLY' } });
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Duplicate' } });
    fireEvent.click(screen.getByRole('checkbox'));
    rerender(renderReceipt({ ...receipt, event_id: 'new-event', amount: '30.00' }));
    expect(screen.getByRole('alert')).toHaveTextContent('changed');
    expect(screen.getByRole('button', { name: 'Confirm correction' })).toBeDisabled();
    expect(garageApi.correctReceipt).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Close form' }));
    fireEvent.click(screen.getByRole('button', { name: 'Correct receipt' }));
    expect(screen.getByRole('heading', { name: 'Correct receipt ₹30.00' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm correction' })).toBeDisabled();
  });
  it('requires confirmation and preserves the original timestamp when unchanged', async () => {
    vi.mocked(garageApi.correctReceipt).mockResolvedValue({ id: 'corr', reversal_event_id: 'reverse', replacement_event_id: 'new' });
    renderForm(); fireEvent.click(screen.getByRole('button', { name: 'Correct receipt' }));
    expect(screen.getByRole('button', { name: 'Confirm correction' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('What happened?'), { target: { value: 'REVERSE_AND_REPLACE' } });
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Actual Cash / Bank account'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Actual amount'), { target: { value: '35' } });
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Wrong amount' } });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm correction' }));
    await waitFor(() => expect(garageApi.correctReceipt).toHaveBeenCalledWith('company', 'user', 'job', 'receipt', { expected_event_id: 'event', outcome: 'REVERSE_AND_REPLACE', reason: 'Wrong amount', replacement: { account_id: 'account', amount: '35', effective_at: receipt.effective_at } }));
  });
  it('keeps the correction open after a backend rejection', async () => {
    vi.mocked(garageApi.correctReceipt).mockRejectedValue(new Error('Charge exceeded'));
    renderForm(); fireEvent.click(screen.getByRole('button', { name: 'Correct receipt' }));
    fireEvent.change(screen.getByLabelText('What happened?'), { target: { value: 'REVERSE_ONLY' } });
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Duplicate' } });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm correction' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Charge exceeded');
    expect(screen.getByLabelText('Reason')).toHaveValue('Duplicate');
  });
});
