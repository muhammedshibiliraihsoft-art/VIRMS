import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { GarageStatusHistory } from '../GarageStatusHistory';
import { garageApi } from '../../../api/garageApi';

vi.mock('../../../api/garageApi', () => ({ garageApi: { statusHistory: vi.fn() } }));

describe('Garage status history', () => {
  it('fetches history only on request and shows actual transitions', async () => {
    vi.mocked(garageApi.statusHistory).mockResolvedValue({ count: 1, previous: null, next: null, results: [{ version: 1, from_status: 'OPEN', to_status: 'COMPLETED', actor_id: 'actor', created_at: '2026-11-17T00:00:00Z' }] });
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><GarageStatusHistory companyId="company" userId="user" jobId="job" /></QueryClientProvider>);
    expect(garageApi.statusHistory).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Show status history' }));
    expect(await screen.findByText(/Open → Completed/)).toBeInTheDocument();
    expect(garageApi.statusHistory).toHaveBeenCalledWith('company', 'job', 1, expect.any(AbortSignal));
  });
});
