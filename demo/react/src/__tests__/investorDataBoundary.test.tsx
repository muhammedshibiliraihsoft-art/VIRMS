import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from '../App';

describe('Investor-only prototype data boundary', () => {
  it('fails closed when an Investor opens a Company dashboard view directly', () => {
    const previousSearch = window.location.search;
    window.history.replaceState({}, '', `${window.location.pathname}?view=financial`);

    render(<App companyWideRoles={['investor']} loginId="investor-one" />);

    expect(screen.getByText(/Investor-specific dashboard data is not connected/i)).toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /Financial/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/Company Result|Operating Revenue|Total Revenue/)).not.toBeInTheDocument();

    window.history.replaceState({}, '', `${window.location.pathname}${previousSearch}`);
  });

  it('does not show shared Company dashboard or Investor sample data', () => {
    render(<App companyWideRoles={['investor']} loginId="investor-one" />);

    expect(screen.getByText(/Investor-specific dashboard data is not connected/i)).toBeInTheDocument();
    expect(screen.queryByText('Ayaan')).not.toBeInTheDocument();
    expect(screen.queryByText('Sara')).not.toBeInTheDocument();
    expect(screen.queryByText('Total Balance')).not.toBeInTheDocument();

    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    fireEvent.click(within(rail).getByRole('button', { name: 'Investment Management' }));
    const investmentMenu = screen.getByRole('region', { name: 'Investment Management submenu' });
    fireEvent.click(within(investmentMenu).getByRole('button', { name: /Investor Fund/ }));

    expect(screen.getByText(/Investor-specific Fund data is not connected/i)).toBeInTheDocument();
    expect(screen.queryByText('Ayaan')).not.toBeInTheDocument();
    expect(screen.queryByText('Sara')).not.toBeInTheDocument();
  });

  it('does not show shared stock vehicle samples to an Investor-only account', () => {
    render(<App companyWideRoles={['investor']} loginId="investor-one" />);

    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    fireEvent.click(within(rail).getByRole('button', { name: 'Vehicles' }));

    expect(screen.getByText(/Investor-owned Stock Vehicles are not connected/i)).toBeInTheDocument();
    expect(screen.queryByText('Toyota Fortuner')).not.toBeInTheDocument();
    expect(screen.queryByText('Ayaan')).not.toBeInTheDocument();
  });

  it('hides an already-open Vehicle detail if Company role context changes to Investor-only', () => {
    const { rerender } = render(<App companyWideRoles={['owner']} loginId="owner-one" />);
    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    fireEvent.click(within(rail).getByRole('button', { name: 'Vehicles' }));
    fireEvent.click(screen.getAllByRole('button', { name: 'Details' })[0]);

    expect(screen.getByRole('button', { name: 'Back to Vehicles' })).toBeInTheDocument();

    rerender(<App companyWideRoles={['investor']} loginId="investor-one" />);

    expect(screen.getByText(/not available for the current Company role/i)).toBeInTheDocument();
    expect(screen.queryByText(/Ayaan Rahman|Jeep Wrangler Rubicon/)).not.toBeInTheDocument();
  });

  it('does not render report links that Investor role navigation denies', () => {
    render(<App companyWideRoles={['investor']} loginId="investor-one" />);
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
