import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { GarageCustomerHistory } from '../GarageCustomerHistory';
import { garageApi } from '../../../api/garageApi';

vi.mock('../../../api/garageApi', () => ({ garageApi: { charges: vi.fn(), receipts: vi.fn(), customerCostHistory: vi.fn() } }));
const renderHistory = (kind: 'charges' | 'receipts' | 'cost', costId?: string) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><GarageCustomerHistory companyId="company" userId="user" jobId="job" kind={kind} costId={costId} onClose={() => {}} /></QueryClientProvider>);

describe('Garage customer history', () => {
  it('loads receipt history from its scoped endpoint', async () => {
    vi.mocked(garageApi.receipts).mockResolvedValue({ count: 1, previous: null, next: null, results: [{ id: 'receipt', amount: '40.00', reference: 'REF-1', effective_at: '2026-11-17T00:00:00Z' }] } as never);
    renderHistory('receipts');
    expect(await screen.findByText(/REF-1/)).toBeInTheDocument();
    expect(garageApi.receipts).toHaveBeenCalledWith('company', 'job', 1, expect.any(AbortSignal));
  });
  it('reports an unavailable correction history without inventing entries', async () => {
    vi.mocked(garageApi.customerCostHistory).mockRejectedValue(new Error('Unavailable'));
    renderHistory('cost', 'cost');
    expect(await screen.findByRole('alert')).toHaveTextContent('History could not be loaded');
  });
});
