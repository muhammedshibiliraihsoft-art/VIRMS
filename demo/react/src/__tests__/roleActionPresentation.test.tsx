import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../App';

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({ status: 'anonymous', user: null, currentCompany: null }),
}));

describe('role-aware business action presentation', () => {
  it('hides dashboard write entry points from an Owner while keeping them for an Accountant', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
    const { rerender } = render(
      <QueryClientProvider client={queryClient}><App companyWideRoles={['owner']} /></QueryClientProvider>
    );

    expect(screen.queryByRole('button', { name: 'Record Receipt' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'New Sale' })).not.toBeInTheDocument();

    rerender(
      <QueryClientProvider client={queryClient}><App companyWideRoles={['accountant']} /></QueryClientProvider>
    );
    expect(screen.getByRole('button', { name: 'Record Receipt' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'New Sale' })).toBeInTheDocument();
  });
});
