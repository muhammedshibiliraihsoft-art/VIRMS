import React, { useState, useEffect } from 'react';
import {
  Building2,
  MapPin,
  Users,
  UserCheck,
  ShieldCheck,
  Network,
  Settings2,
  ArrowUpRight,
  LogOut,
  Sun,
  Moon,
  Shield,
  LayoutDashboard,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from './AuthContext';

export interface BackOfficePageProps {
  onLogout: () => void | Promise<void>;
}

interface AdminItem {
  id: string;
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;
}

interface AdminGroup {
  groupTitle: string;
  items: AdminItem[];
}

const ADMIN_GROUPS: AdminGroup[] = [
  {
    groupTitle: 'Companies & locations',
    items: [
      {
        id: 'companies',
        title: 'Companies',
        description: 'Manage tenant companies and organizational entities.',
        href: '/admin/tenants/tenant/',
        icon: Building2,
      },
      {
        id: 'branches',
        title: 'Branches',
        description: 'Manage company branches and workshop locations.',
        href: '/admin/tenants/branch/',
        icon: MapPin,
      },
    ],
  },
  {
    groupTitle: 'Accounts & access',
    items: [
      {
        id: 'users',
        title: 'User accounts',
        description: 'Manage platform and company user logins and authentication.',
        href: '/admin/accounts/user/',
        icon: Users,
      },
      {
        id: 'memberships',
        title: 'Company memberships',
        description: 'Manage user associations with tenant companies.',
        href: '/admin/tenants/tenantmembership/',
        icon: UserCheck,
      },
      {
        id: 'role-grants',
        title: 'Company role grants',
        description: 'Manage tenant-level and company-wide role permissions.',
        href: '/admin/tenants/companyrolegrant/',
        icon: ShieldCheck,
      },
      {
        id: 'branch-assignments',
        title: 'Branch assignments',
        description: 'Manage user assignments to specific branch locations.',
        href: '/admin/tenants/branchassignment/',
        icon: Network,
      },
    ],
  },
  {
    groupTitle: 'Company configuration',
    items: [
      {
        id: 'modules',
        title: 'Module configuration',
        description: 'Configure versioned tenant module states and features.',
        href: '/admin/tenants/companymodulestate/configure/',
        icon: Settings2,
      },
    ],
  },
];

export const BackOfficePage: React.FC<BackOfficePageProps> = ({ onLogout }) => {
  const { user, currentCompany } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [activeSection, setActiveSection] = useState<'all' | 'companies' | 'accounts' | 'config'>('all');
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof document !== 'undefined') {
      const stored = document.documentElement.getAttribute('data-theme');
      if (stored === 'dark' || stored === 'light') return stored;
    }
    return 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const handleLogout = async () => {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await onLogout();
    } finally {
      setLoggingOut(false);
    }
  };

  const filteredGroups = ADMIN_GROUPS.filter((g) => {
    if (activeSection === 'all') return true;
    if (activeSection === 'companies') return g.groupTitle === 'Companies & locations';
    if (activeSection === 'accounts') return g.groupTitle === 'Accounts & access';
    if (activeSection === 'config') return g.groupTitle === 'Company configuration';
    return true;
  });

  return (
    <div
      data-theme={theme}
      className={`min-h-screen min-h-[100dvh] flex flex-col md:flex-row bg-[var(--theme-bg-app,#fffdfb)] text-[#18181b] dark:text-gray-100 ${
        theme === 'dark' ? 'dark' : ''
      }`}
    >
      {/* =========================================================================
          DESKTOP SIDEBAR RAIL (Matching VIRMS Narrow Sidebar Style on md+)
          Provides vertical icon navigation, identity, theme toggle & logout
         ========================================================================= */}
      <aside
        aria-label="Platform administration navigation"
        className="hidden md:flex flex-col items-center justify-between w-16 lg:w-20 shrink-0 border-r border-gray-200/80 dark:border-zinc-800 bg-white/70 dark:bg-zinc-900/70 backdrop-blur-md py-5 sticky top-0 h-screen h-[100dvh] z-20"
      >
        {/* Top: VIRMS Identity */}
        <div className="flex flex-col items-center gap-4">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--theme-primary)] text-base font-extrabold text-white shadow-sm"
            aria-hidden="true"
          >
            V
          </div>

          {/* Sidebar Nav Items */}
          <nav className="flex flex-col items-center gap-2 mt-4" aria-label="Desktop sections">
            <button
              type="button"
              onClick={() => setActiveSection('all')}
              title="All Destinations"
              aria-label="All Destinations"
              className={`p-2.5 rounded-xl transition-all cursor-pointer ${
                activeSection === 'all'
                  ? 'bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] font-bold shadow-2xs'
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              <LayoutDashboard className="w-5 h-5" />
            </button>
            <button
              type="button"
              onClick={() => setActiveSection('companies')}
              title="Companies & locations"
              aria-label="Companies & locations"
              className={`p-2.5 rounded-xl transition-all cursor-pointer ${
                activeSection === 'companies'
                  ? 'bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] font-bold shadow-2xs'
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              <Building2 className="w-5 h-5" />
            </button>
            <button
              type="button"
              onClick={() => setActiveSection('accounts')}
              title="Accounts & access"
              aria-label="Accounts & access"
              className={`p-2.5 rounded-xl transition-all cursor-pointer ${
                activeSection === 'accounts'
                  ? 'bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] font-bold shadow-2xs'
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              <Users className="w-5 h-5" />
            </button>
            <button
              type="button"
              onClick={() => setActiveSection('config')}
              title="Company configuration"
              aria-label="Company configuration"
              className={`p-2.5 rounded-xl transition-all cursor-pointer ${
                activeSection === 'config'
                  ? 'bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] font-bold shadow-2xs'
                  : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              <Settings2 className="w-5 h-5" />
            </button>
          </nav>
        </div>

        {/* Bottom: Theme Toggle & Logout on Desktop */}
        <div className="flex flex-col items-center gap-3">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="p-2.5 rounded-xl text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            aria-label="Sign out"
            title="Sign out"
            className="p-2.5 rounded-xl text-rose-600 hover:text-rose-700 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer disabled:opacity-50"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </aside>

      {/* =========================================================================
          MAIN WORKSPACE CONTENT COLUMN
         ========================================================================= */}
      <div className="flex-1 min-w-0 flex flex-col min-h-screen min-h-[100dvh] pb-16 md:pb-0">
        {/* Top Header Bar */}
        <header className="border-b border-gray-200/80 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md sticky top-0 z-30">
          <div className="max-w-6xl mx-auto px-2.5 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between gap-1.5 sm:gap-4">
            {/* Mobile Logo & Brand Title */}
            <div className="flex items-center gap-2 sm:gap-3 shrink-0">
              <span
                className="flex md:hidden h-8 w-8 items-center justify-center rounded-xl bg-[var(--theme-primary)] text-sm font-extrabold text-white shadow-sm shrink-0"
                aria-hidden="true"
              >
                V
              </span>
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-[var(--theme-primary)]">
                  VIRMS
                </span>
                <span className="text-gray-300 dark:text-zinc-700 hidden sm:inline" aria-hidden="true">|</span>
                <span className="text-xs sm:text-sm font-semibold text-gray-800 dark:text-gray-200 hidden sm:inline">
                  Platform Back Office
                </span>
              </div>
            </div>

            {/* Header Right Actions */}
            <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
              {/* Direct Link to Django Admin Root */}
              <a
                href="/admin/"
                title="Open Django Admin"
                className="inline-flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-700 hover:text-gray-950 dark:text-gray-300 dark:hover:text-white bg-gray-100 hover:bg-gray-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] shrink-0"
              >
                <span><span className="hidden sm:inline">Django </span>Admin</span>
                <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
              </a>

              {/* Mobile-only theme toggle (Desktop has it in sidebar) */}
              <button
                type="button"
                onClick={toggleTheme}
                aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                className="md:hidden p-1.5 rounded-lg text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer shrink-0"
              >
                {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>

              {/* Sign Out Action Button */}
              <button
                type="button"
                onClick={handleLogout}
                disabled={loggingOut}
                className="inline-flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] disabled:opacity-50 cursor-pointer shadow-xs shrink-0"
              >
                <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
                <span>{loggingOut ? 'Signing out…' : 'Sign out'}</span>
              </button>
            </div>
          </div>
        </header>

        {/* Dashboard Main View Area */}
        <main className="flex-1 max-w-6xl w-full mx-auto px-3.5 sm:px-6 lg:px-8 py-5 sm:py-8">
          {/* Orientation & Heading Banner */}
          <div className="mb-5 sm:mb-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 sm:pb-5 border-b border-gray-200/80 dark:border-zinc-800">
              <div>
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-gray-950 dark:text-white tracking-tight">
                  Platform Back Office
                </h1>
                <p className="mt-1 text-xs sm:text-sm text-gray-600 dark:text-gray-400 max-w-2xl leading-relaxed">
                  Administrative navigation and orientation gateway. Select an administrative area below to manage records in Django Admin.
                </p>

                {/* Authenticated Login ID & Role Badge */}
                {user?.login_id && (
                  <div className="flex items-center gap-2 mt-2.5">
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-100 dark:bg-zinc-800 text-xs text-gray-700 dark:text-gray-300 border border-gray-200/60 dark:border-zinc-700/60">
                      <Shield className="w-3.5 h-3.5 text-[var(--theme-primary)] shrink-0" aria-hidden="true" />
                      <span className="font-semibold">{user.login_id}</span>
                      <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase tracking-wider bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] shrink-0">
                        Platform
                      </span>
                      {currentCompany?.name && (
                        <>
                          <span className="text-gray-300 dark:text-zinc-600" aria-hidden="true">•</span>
                          <span className="text-gray-500 dark:text-gray-400">{currentCompany.name}</span>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Source of Truth Status Pill */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 text-xs font-semibold self-start sm:self-auto shrink-0">
                <span className="w-2 h-2 rounded-full bg-amber-500" aria-hidden="true" />
                <span>Source of truth: Django Admin</span>
              </div>
            </div>

            {/* Desktop Section Selector Pills */}
            <div className="hidden md:flex items-center gap-2 mt-4">
              <button
                type="button"
                onClick={() => setActiveSection('all')}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                  activeSection === 'all'
                    ? 'bg-[#18181b] text-white dark:bg-white dark:text-black shadow-xs'
                    : 'bg-black/5 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-black/10'
                }`}
              >
                All Areas
              </button>
              <button
                type="button"
                onClick={() => setActiveSection('companies')}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                  activeSection === 'companies'
                    ? 'bg-[#18181b] text-white dark:bg-white dark:text-black shadow-xs'
                    : 'bg-black/5 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-black/10'
                }`}
              >
                Companies & Locations
              </button>
              <button
                type="button"
                onClick={() => setActiveSection('accounts')}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                  activeSection === 'accounts'
                    ? 'bg-[#18181b] text-white dark:bg-white dark:text-black shadow-xs'
                    : 'bg-black/5 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-black/10'
                }`}
              >
                Accounts & Access
              </button>
              <button
                type="button"
                onClick={() => setActiveSection('config')}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                  activeSection === 'config'
                    ? 'bg-[#18181b] text-white dark:bg-white dark:text-black shadow-xs'
                    : 'bg-black/5 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-black/10'
                }`}
              >
                Module Configuration
              </button>
            </div>
          </div>

          {/* Grouped Admin Destination Cards */}
          <div className="space-y-6 sm:space-y-8">
            {filteredGroups.map((group, groupIndex) => {
              const headingId = `admin-group-${groupIndex}`;
              return (
                <section key={group.groupTitle} aria-labelledby={headingId} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h2
                      id={headingId}
                      className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400"
                    >
                      {group.groupTitle}
                    </h2>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500 font-medium">
                      {group.items.length} {group.items.length === 1 ? 'destination' : 'destinations'}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    {group.items.map((item) => {
                      const IconComponent = item.icon;
                      return (
                        <a
                          key={item.href}
                          href={item.href}
                          className="dashboard-card-solid rounded-2xl p-4 sm:p-5 flex items-start justify-between gap-3 group transition-all duration-150 hover:border-[var(--theme-primary-border)] hover:bg-[var(--theme-primary-subtle)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] min-h-[44px]"
                        >
                          <div className="flex items-start gap-3.5 min-w-0">
                            <div
                              className="w-10 h-10 rounded-xl bg-[var(--theme-primary-soft)] text-[var(--theme-primary)] flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform duration-150"
                              aria-hidden="true"
                            >
                              <IconComponent className="w-5 h-5" />
                            </div>
                            <div className="space-y-1 min-w-0">
                              <h3 className="text-sm font-bold text-gray-950 dark:text-white group-hover:text-[var(--theme-primary)] transition-colors">
                                {item.title}
                              </h3>
                              <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                                {item.description}
                              </p>
                            </div>
                          </div>
                          <div
                            className="w-7 h-7 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center text-gray-400 group-hover:text-[var(--theme-primary)] group-hover:bg-[var(--theme-primary-soft)] transition-colors shrink-0 mt-0.5"
                            aria-hidden="true"
                          >
                            <ArrowUpRight className="w-4 h-4" />
                          </div>
                        </a>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        </main>

        {/* Subtle Footer */}
        <footer className="mt-auto border-t border-gray-200/60 dark:border-zinc-800/80 py-4 px-4 sm:px-6 lg:px-8 bg-white/40 dark:bg-zinc-900/40">
          <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs text-gray-500 dark:text-gray-400 gap-2">
            <div className="flex items-center gap-1.5 font-medium">
              <span className="font-bold text-gray-700 dark:text-gray-300">VIRMS Platform</span>
              <span>·</span>
              <span>Back Office Gateway</span>
            </div>
            <div>Django Admin remains the authoritative source for administration actions</div>
          </div>
        </footer>
      </div>

      {/* =========================================================================
          MOBILE BOTTOM NAVIGATION (Phone only: < md)
          Gives quick one-thumb navigation between sections and external Django Admin
         ========================================================================= */}
      <nav
        aria-label="Mobile bottom navigation"
        className="md:hidden fixed bottom-0 left-0 right-0 h-14 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md border-t border-gray-200 dark:border-zinc-800 flex items-center justify-around px-2 z-40 select-none"
      >
        <button
          type="button"
          onClick={() => setActiveSection('all')}
          className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg text-[10px] font-semibold transition cursor-pointer ${
            activeSection === 'all'
              ? 'text-[var(--theme-primary)] font-bold'
              : 'text-gray-500 dark:text-gray-400'
          }`}
        >
          <LayoutDashboard className="w-4 h-4 mb-0.5" />
          <span>All</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSection('companies')}
          className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg text-[10px] font-semibold transition cursor-pointer ${
            activeSection === 'companies'
              ? 'text-[var(--theme-primary)] font-bold'
              : 'text-gray-500 dark:text-gray-400'
          }`}
        >
          <Building2 className="w-4 h-4 mb-0.5" />
          <span>Companies</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSection('accounts')}
          className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg text-[10px] font-semibold transition cursor-pointer ${
            activeSection === 'accounts'
              ? 'text-[var(--theme-primary)] font-bold'
              : 'text-gray-500 dark:text-gray-400'
          }`}
        >
          <Users className="w-4 h-4 mb-0.5" />
          <span>Accounts</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSection('config')}
          className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg text-[10px] font-semibold transition cursor-pointer ${
            activeSection === 'config'
              ? 'text-[var(--theme-primary)] font-bold'
              : 'text-gray-500 dark:text-gray-400'
          }`}
        >
          <Settings2 className="w-4 h-4 mb-0.5" />
          <span>Config</span>
        </button>

        <a
          href="/admin/"
          className="flex flex-col items-center justify-center py-1 px-3 rounded-lg text-[10px] font-semibold text-gray-500 dark:text-gray-400 hover:text-[var(--theme-primary)] transition"
        >
          <ExternalLink className="w-4 h-4 mb-0.5" />
          <span>Admin ↗</span>
        </a>
      </nav>
    </div>
  );
};

export default BackOfficePage;
