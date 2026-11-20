import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';

const mocks = vi.hoisted(() => ({ useAuth: vi.fn(), investorPortalSelf: vi.fn() }));

vi.mock('../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../api/phase5Api', () => ({
  phase5Api: {
    investorPortalSelf: mocks.investorPortalSelf,
    requestInvestorExit: vi.fn(),
    requestInvestorExitCancellation: vi.fn(),
  },
}));

function renderApp(companyWideRoles: string[], loginId: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(<QueryClientProvider client={queryClient}><App companyWideRoles={companyWideRoles} loginId={loginId} /></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.useAuth.mockReturnValue({
    status: 'authenticated',
    user: { id: '11111111-1111-4111-8111-111111111111' },
    currentCompany: { id: '22222222-2222-4222-8222-222222222222' },
    error: null,
    login: vi.fn(), changePassword: vi.fn(), logout: vi.fn(), retryBootstrap: vi.fn(),
  });
  mocks.investorPortalSelf.mockRejectedValue(new Error('Private Investor profile unavailable'));
});

describe('Investor-only prototype data boundary', () => {
  it('fails closed when an Investor opens a Company dashboard view directly', async () => {
    const previousSearch = window.location.search;
    window.history.replaceState({}, '', `${window.location.pathname}?view=financial`);

    renderApp(['investor'], 'investor-one');

    expect(await screen.findByText(/Investor information is unavailable/i)).toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /Financial/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/Company Result|Operating Revenue|Total Revenue/)).not.toBeInTheDocument();

    window.history.replaceState({}, '', `${window.location.pathname}${previousSearch}`);
  });

  it('does not show shared Company dashboard or Investor sample data', async () => {
    renderApp(['investor'], 'investor-one');

    expect(await screen.findByText(/Investor information is unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText('Ayaan')).not.toBeInTheDocument();
    expect(screen.queryByText('Sara')).not.toBeInTheDocument();
    expect(screen.queryByText('Total Balance')).not.toBeInTheDocument();

    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    fireEvent.click(within(rail).getByRole('button', { name: 'Investment Management' }));
    const investmentMenu = screen.getByRole('region', { name: 'Investment Management submenu' });
    fireEvent.click(within(investmentMenu).getByRole('button', { name: /Investor Fund/ }));

    expect(await screen.findByText(/Investor information is unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText('Ayaan')).not.toBeInTheDocument();
    expect(screen.queryByText('Sara')).not.toBeInTheDocument();
  });

  it('does not show shared stock vehicle samples to an Investor-only account', () => {
    renderApp(['investor'], 'investor-one');

    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    fireEvent.click(within(rail).getByRole('button', { name: 'Vehicles' }));

    expect(screen.getByText(/Investor-owned Stock Vehicles are not connected/i)).toBeInTheDocument();
    expect(screen.queryByText('Toyota Fortuner')).not.toBeInTheDocument();
    expect(screen.queryByText('Ayaan')).not.toBeInTheDocument();
  });

  it('hides an already-open Vehicle detail if Company role context changes to Investor-only', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
    const { rerender } = render(<QueryClientProvider client={queryClient}><App companyWideRoles={['owner']} loginId="owner-one" /></QueryClientProvider>);
    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    fireEvent.click(within(rail).getByRole('button', { name: 'Vehicles' }));
    fireEvent.click(screen.getAllByRole('button', { name: 'Details' })[0]);

    expect(screen.getByRole('button', { name: 'Back to Vehicles' })).toBeInTheDocument();

    rerender(<QueryClientProvider client={queryClient}><App companyWideRoles={['investor']} loginId="investor-one" /></QueryClientProvider>);

    expect(screen.getByText(/not available for the current Company role/i)).toBeInTheDocument();
    expect(screen.queryByText(/Ayaan Rahman|Jeep Wrangler Rubicon/)).not.toBeInTheDocument();
  });

  it('does not render report links that Investor role navigation denies', () => {
    renderApp(['investor'], 'investor-one');
    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });

    fireEvent.click(within(rail).getByRole('button', { name: 'Investment Management' }));
    let menu = screen.getByRole('region', { name: 'Investment Management submenu' });
    fireEvent.click(within(menu).getByRole('button', { name: /Investor Profit & Interim/ }));
    expect(screen.queryByRole('button', { name: /Explore Reports/ })).not.toBeInTheDocument();

    fireEvent.click(within(rail).getByRole('button', { name: 'Investment Management' }));
    menu = screen.getByRole('region', { name: 'Investment Management submenu' });
    fireEvent.click(within(menu).getByRole('button', { name: /Reconciliation & Settlement/ }));
    expect(screen.queryByRole('button', { name: /Explore Reports/ })).not.toBeInTheDocument();
  });
});
