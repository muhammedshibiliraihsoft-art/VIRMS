import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AppShell } from '../AppShell';

function renderShell(
  companyWideRoles: string[],
  branchContexts: Array<{ id: string; name: string; roles: string[] }> = []
) {
  const onSelectRoute = vi.fn();
  const rendered = render(
    <AppShell
      activeRoute="Dashboard"
      activeTab="Overview"
      theme="light"
      onToggleTheme={vi.fn()}
      onSelectRoute={onSelectRoute}
      onSelectTab={vi.fn()}
      garages={[]}
      selectedGarage="all"
      onSelectGarage={vi.fn()}
      onRefresh={vi.fn()}
      statusMessages={[]}
      onDismissStatus={vi.fn()}
      companyName="Example Company"
      companyWideRoles={companyWideRoles}
      branchContexts={branchContexts}
    >
      <div>Current demo page</div>
    </AppShell>
  );
  return { ...rendered, onSelectRoute };
}

describe('AppShell role-filtered navigation', () => {
  it('applies Owner visibility to both rail and quick tabs', () => {
    renderShell(['owner']);

    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    expect(rail).toHaveAccessibleName('Main Navigation Rail');
    expect(within(rail).getByRole('button', { name: 'Vehicles' })).toBeInTheDocument();
    expect(within(rail).getByRole('button', { name: 'Reports' })).toBeInTheDocument();
    expect(within(rail).queryByRole('button', { name: 'Inventory' })).not.toBeInTheDocument();

    const quickNavigation = screen.getByRole('navigation', { name: 'Quick section navigation' });
    expect(quickNavigation).toHaveTextContent('Overview');
    expect(quickNavigation).toHaveTextContent('Vehicles');
    expect(quickNavigation).not.toHaveTextContent('Inventory');
  });

  it('keeps unsupported Inventory hidden from Accountant navigation', () => {
    renderShell(['accountant']);

    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    expect(within(rail).getByRole('button', { name: 'Vehicles' })).toBeInTheDocument();
    expect(within(rail).getByRole('button', { name: 'Reports' })).toBeInTheDocument();
    expect(within(rail).queryByRole('button', { name: 'Inventory' })).not.toBeInTheDocument();

    const quickNavigation = screen.getByRole('navigation', { name: 'Quick section navigation' });
    expect(quickNavigation).not.toHaveTextContent('Inventory');
  });

  it('keeps Investor navigation within own-portfolio areas and hides Company reports', () => {
    renderShell(['investor']);

    const rail = screen.getByRole('navigation', { name: 'Main Navigation Rail' });
    expect(within(rail).getByRole('button', { name: 'Vehicles' })).toBeInTheDocument();
    expect(within(rail).getByRole('button', { name: 'Investment Management' })).toBeInTheDocument();
    expect(within(rail).queryByRole('button', { name: 'Company Accounting' })).not.toBeInTheDocument();
    expect(within(rail).queryByRole('button', { name: 'Reports' })).not.toBeInTheDocument();

    fireEvent.click(within(rail).getByRole('button', { name: 'Investment Management' }));
    expect(screen.getAllByText('Investor Fund').length).toBeGreaterThan(0);
    expect(screen.queryByText('Vehicle Sales')).not.toBeInTheDocument();
    expect(screen.queryByText('Collections')).not.toBeInTheDocument();
  });

  it('keeps Media business routes out of the mobile menu when no Media screen exists', () => {
    renderShell(['media']);
    fireEvent.click(screen.getByRole('button', { name: 'Open mobile navigation menu' }));
    fireEvent.click(screen.getByRole('button', { name: 'Toggle Settings sub-items' }));

    expect(screen.getByRole('button', { name: 'Close mobile navigation menu' })).toBeInTheDocument();
    expect(screen.getByText('Appearance & Theme')).toBeInTheDocument();
    expect(screen.queryByText('Vehicles')).not.toBeInTheDocument();
    expect(screen.queryByText('Investor Fund')).not.toBeInTheDocument();
    expect(screen.queryByText('Garages / Branches')).not.toBeInTheDocument();
  });

  it('does not expose any business navigation for unknown or Platform roles', () => {
    const { rerender } = renderShell(['future_role']);
    expect(screen.getByRole('navigation', { name: 'Main Navigation Rail' }).children).toHaveLength(0);
    expect(screen.getByRole('navigation', { name: 'Quick section navigation' }).children).toHaveLength(0);

    rerender(
      <AppShell
        activeRoute="Dashboard"
        activeTab="Overview"
        theme="light"
        onToggleTheme={vi.fn()}
        onSelectRoute={vi.fn()}
        onSelectTab={vi.fn()}
        garages={[]}
        selectedGarage="all"
        onSelectGarage={vi.fn()}
        onRefresh={vi.fn()}
        statusMessages={[]}
        onDismissStatus={vi.fn()}
        companyWideRoles={['back_office']}
      >
        <div>Current demo page</div>
      </AppShell>
    );
    expect(screen.getByRole('navigation', { name: 'Main Navigation Rail' }).children).toHaveLength(0);
    expect(screen.getByRole('navigation', { name: 'Quick section navigation' }).children).toHaveLength(0);
  });

  it('renders server-provided Branch roles as context without adding Company-wide navigation', () => {
    renderShell([], [{ id: 'd4c80f18-2255-4f68-b835-83b6a08103a1', name: 'North Branch', roles: ['accountant'] }]);

    fireEvent.click(screen.getByRole('button', { name: /All Garages/ }));
    expect(screen.getByText(/North Branch/)).toBeInTheDocument();
    expect(screen.getByText(/North Branch · Roles: accountant/)).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Main Navigation Rail' }).children).toHaveLength(0);
  });

  it('marks the prototype avatar initials as decorative inside the context filter', () => {
    renderShell(['owner']);

    const filter = screen.getByRole('button', { name: /Filter prototype garage data/ });
    expect(within(filter).getByText('OP')).toHaveAttribute('aria-hidden', 'true');
  });

  it('routes the desktop Settings shortcut to an allowed route', () => {
    const { onSelectRoute } = renderShell(['media']);

    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));

    expect(onSelectRoute).toHaveBeenCalledWith('Appearance & Theme');
  });

  it('traps keyboard focus in the mobile drawer and restores the opener on close', () => {
    renderShell(['accountant']);

    const opener = screen.getByRole('button', { name: 'Open mobile navigation menu' });
    expect(opener).toHaveAttribute('aria-expanded', 'false');
    opener.focus();
    fireEvent.click(opener);
    expect(opener).toHaveAttribute('aria-expanded', 'true');

    const drawer = screen.getByRole('dialog', { name: 'Mobile navigation menu' });
    const close = within(drawer).getByRole('button', { name: 'Close mobile navigation menu' });
    const logout = within(drawer).getByRole('button', { name: 'Log Out' });
    expect(close).toHaveFocus();

    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(logout).toHaveFocus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(close).toHaveFocus();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog', { name: 'Mobile navigation menu' })).not.toBeInTheDocument();
    expect(opener).toHaveAttribute('aria-expanded', 'false');
    expect(opener).toHaveFocus();
  });
});
