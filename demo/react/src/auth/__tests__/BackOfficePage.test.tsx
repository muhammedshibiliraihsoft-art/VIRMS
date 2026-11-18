import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { BackOfficePage } from '../BackOfficePage';
import { AuthContextValue } from '../AuthContext';

const mockUseAuth = vi.fn();
vi.mock('../AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

const platformUser: AuthContextValue['user'] = {
  id: 'usr-platform-001',
  login_id: 'ops-admin',
  must_change_password: false,
  roles: ['back_office'],
  tenant_ids: [],
  companies: [],
  company_context_truncated: false,
};

describe('BackOfficePage', () => {
  it('renders the Platform Back Office landing page with title and user Login ID', () => {
    mockUseAuth.mockReturnValue({
      user: platformUser,
      currentCompany: null,
      status: 'authenticated',
      logout: vi.fn(),
    });

    render(<BackOfficePage onLogout={vi.fn()} />);

    expect(screen.getByRole('heading', { level: 1, name: 'Platform Back Office' })).toBeInTheDocument();
    expect(screen.getByText('ops-admin')).toBeInTheDocument();
    expect(screen.getByText('Platform')).toBeInTheDocument();
  });

  it('renders all 7 specified administrative destinations with exact Django Admin hrefs as regular anchors', () => {
    mockUseAuth.mockReturnValue({
      user: platformUser,
      currentCompany: null,
      status: 'authenticated',
      logout: vi.fn(),
    });

    render(<BackOfficePage onLogout={vi.fn()} />);

    const expectedLinks = [
      { name: /^Companies\b/, href: '/admin/tenants/tenant/' },
      { name: /^Branches\b/, href: '/admin/tenants/branch/' },
      { name: /^User accounts\b/, href: '/admin/accounts/user/' },
      { name: /^Company memberships\b/, href: '/admin/tenants/tenantmembership/' },
      { name: /^Company role grants\b/, href: '/admin/tenants/companyrolegrant/' },
      { name: /^Branch assignments\b/, href: '/admin/tenants/branchassignment/' },
      { name: /^Module configuration\b/, href: '/admin/tenants/companymodulestate/configure/' },
    ];

    for (const { name, href } of expectedLinks) {
      const link = screen.getByRole('link', { name });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', href);
      expect(link.tagName.toLowerCase()).toBe('a');
    }
  });

  it('renders the direct link to the Django Admin root', () => {
    mockUseAuth.mockReturnValue({
      user: platformUser,
      currentCompany: null,
      status: 'authenticated',
      logout: vi.fn(),
    });

    render(<BackOfficePage onLogout={vi.fn()} />);

    const rootAdminLinks = screen.getAllByRole('link', { name: /Django Admin/i });
    expect(rootAdminLinks.length).toBeGreaterThan(0);
    expect(rootAdminLinks[0]).toHaveAttribute('href', '/admin/');
  });

  it('calls onLogout when the Sign out button is clicked', async () => {
    const onLogout = vi.fn().mockResolvedValue(undefined);
    mockUseAuth.mockReturnValue({
      user: platformUser,
      currentCompany: null,
      status: 'authenticated',
      logout: vi.fn(),
    });

    render(<BackOfficePage onLogout={onLogout} />);

    const signOutBtns = screen.getAllByRole('button', { name: /Sign out/i });
    expect(signOutBtns.length).toBeGreaterThan(0);
    fireEvent.click(signOutBtns[0]);

    expect(onLogout).toHaveBeenCalledTimes(1);
  });

  it('toggles light/dark theme when theme button is clicked', () => {
    mockUseAuth.mockReturnValue({
      user: platformUser,
      currentCompany: null,
      status: 'authenticated',
      logout: vi.fn(),
    });

    render(<BackOfficePage onLogout={vi.fn()} />);

    const themeToggles = screen.getAllByRole('button', { name: /Switch to dark mode/i });
    expect(themeToggles.length).toBeGreaterThan(0);

    fireEvent.click(themeToggles[0]);
    expect(screen.getAllByRole('button', { name: /Switch to light mode/i })[0]).toBeInTheDocument();
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('does not display Company or Branch context when not in authenticated server context', () => {
    mockUseAuth.mockReturnValue({
      user: platformUser,
      currentCompany: null,
      status: 'authenticated',
      logout: vi.fn(),
    });

    render(<BackOfficePage onLogout={vi.fn()} />);

    expect(screen.queryByText(/Example Company/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Branch:/i)).not.toBeInTheDocument();
  });
});
