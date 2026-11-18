import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LabourPaymentCorrection } from '../LabourPaymentCorrection';
import { garageApi } from '../../../api/garageApi';
import { accountingAccounts } from '../../../api/accountingApi';

vi.mock('../../../api/garageApi', () => ({ garageApi: { labourCorrectionHistory: vi.fn(), correctLabourPayment: vi.fn() } }));
vi.mock('../../../api/accountingApi', () => ({ accountingAccounts: vi.fn() }));
const payment = { id: 'payment', event_id: 'event', actor_id: 'actor', amount: '100.00', effective_at: '2026-10-01T05:00:30.123456Z', note: '' };
beforeEach(() => { vi.resetAllMocks(); vi.mocked(accountingAccounts).mockResolvedValue([{ id: 'account', label: 'Cash', account_type: 'CASH', is_active: true }]); });
const renderForm = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><LabourPaymentCorrection companyId="company" userId="user" personId="person" payment={payment} canCorrect onBusyChange={() => {}} /></QueryClientProvider>);

describe('Labour payment correction', () => {
  it('blocks a form when a refreshed payment has changed since it was opened', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
    const renderPayment = (row: typeof payment) => <QueryClientProvider client={client}><LabourPaymentCorrection companyId="company" userId="user" personId="person" payment={row} canCorrect onBusyChange={() => {}} /></QueryClientProvider>;
    const { rerender } = render(renderPayment(payment));
    fireEvent.click(screen.getByRole('button', { name: 'Correct payment' }));
    fireEvent.change(screen.getByLabelText('What happened?'), { target: { value: 'REVERSE_ONLY' } });
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Duplicate' } });
    fireEvent.click(screen.getByRole('checkbox'));
    rerender(renderPayment({ ...payment, event_id: 'new-event', amount: '80.00' }));
    expect(screen.getByRole('alert')).toHaveTextContent('changed');
    expect(screen.getByRole('button', { name: 'Confirm correction' })).toBeDisabled();
    expect(garageApi.correctLabourPayment).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Close form' }));
    fireEvent.click(screen.getByRole('button', { name: 'Correct payment' }));
    expect(screen.getByRole('heading', { name: 'Correct payment ₹80.00' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm correction' })).toBeDisabled();
  });
  it('requires an explicit decision and confirmation and preserves the original timestamp', async () => {
    vi.mocked(garageApi.correctLabourPayment).mockResolvedValue({ id: 'correction', reversal_event_id: 'reverse', replacement_event_id: 'new' });
    renderForm(); fireEvent.click(screen.getByRole('button', { name: 'Correct payment' }));
    expect(screen.getByRole('button', { name: 'Confirm correction' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('What happened?'), { target: { value: 'REVERSE_AND_REPLACE' } });
    await screen.findByRole('option', { name: 'Cash · CASH' });
    fireEvent.change(screen.getByLabelText('Actual Cash / Bank account'), { target: { value: 'account' } });
    fireEvent.change(screen.getByLabelText('Actual amount'), { target: { value: '80' } });
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Wrong amount' } });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm correction' }));
    await waitFor(() => expect(garageApi.correctLabourPayment).toHaveBeenCalledWith('company', 'user', 'person', 'payment', { expected_event_id: 'event', outcome: 'REVERSE_AND_REPLACE', reason: 'Wrong amount', replacement: { account_id: 'account', amount: '80', effective_at: payment.effective_at } }));
  });
  it('leaves the selected details available after a failed correction', async () => {
    vi.mocked(garageApi.correctLabourPayment).mockRejectedValue(new Error('Changed by another user'));
    renderForm(); fireEvent.click(screen.getByRole('button', { name: 'Correct payment' }));
    fireEvent.change(screen.getByLabelText('What happened?'), { target: { value: 'REVERSE_ONLY' } });
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Duplicate' } });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm correction' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Changed by another user');
    expect(screen.getByLabelText('Reason')).toHaveValue('Duplicate');
  });
});
