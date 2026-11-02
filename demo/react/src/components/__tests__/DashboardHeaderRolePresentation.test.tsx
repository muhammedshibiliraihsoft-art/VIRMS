import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DashboardHeader } from '../dashboard/DashboardHeader';
import { DashboardViewId } from '../../types/dashboard';

function renderHeader(availableViews?: DashboardViewId[]) {
  return render(
    <DashboardHeader
      activeView="overview"
      onSelectView={vi.fn()}
      lastFetchedAt={Date.now()}
      isRefreshing={false}
      onRefreshActive={vi.fn()}
      autoRefreshInterval={0}
      onSelectAutoRefresh={vi.fn()}
      availableViews={availableViews}
    />
  );
}

describe('DashboardHeader role presentation', () => {
  it('limits Investor dashboard tabs to Overview', () => {
    renderHeader(['overview']);

    const tabs = screen.getByRole('tablist', { name: 'Dashboard perspective switcher' });
    expect(tabs).toHaveTextContent('Overview');
    expect(screen.queryByRole('tab', { name: /Operations/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /Analytics/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /Financial/ })).not.toBeInTheDocument();
  });

  it('preserves all dashboard views for Company-wide roles by default', () => {
    renderHeader();

    expect(screen.getAllByRole('tab')).toHaveLength(4);
  });

  it('keeps the dashboard tab strip scrollable within narrow screens', () => {
    renderHeader();

    expect(screen.getByRole('tablist', { name: 'Dashboard perspective switcher' }))
      .toHaveClass('min-w-0', 'max-w-full', 'overflow-x-auto');
  });
});
