import React from 'react';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../api/apiError';
import { SESSION_EXPIRED_EVENT } from '../../api/client';
import { AuthMe } from '../../api/types';
import { AuthProvider, useAuth } from '../AuthContext';
import { AppRoutes } from '../AppRoutes';

vi.mock('../../api/authApi', () => ({
  authApi: {
    me: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    changePassword: vi.fn(),
    branches: vi.fn(),
  },
}));
vi.mock('../../api/moduleApi', () => ({ companyModuleStates: vi.fn() }));
vi.mock('../../App', () => ({ default: () => <div>Workspace surface</div> }));

import { authApi } from '../../api/authApi';
import { companyModuleStates } from '../../api/moduleApi';
import { queryKeys } from '../../api/queryKeys';

const user: AuthMe = {
  id: '0d6f183a-8cd8-4ed5-9a19-d51c92bbf4ae',
  login_id: 'accountant-1',
  must_change_password: false,
  roles: ['accountant'],
  tenant_ids: ['c9f32d04-1a99-4f01-b583-52ed8b52b41a'],
  companies: [{
    id: 'c9f32d04-1a99-4f01-b583-52ed8b52b41a',
    name: 'Example Company',
    roles: ['accountant'],
    company_wide_roles: ['accountant'],
    branches_truncated: false,
    branches: [],
  }],
  company_context_truncated: false,
};

function renderRoutes(
  path = '/',
  protectedApp: React.ReactNode = <div>Protected application</div>,
  useDefaultWorkspace = false,
) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const rendered = render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <AuthProvider>
          <AppRoutes protectedApp={useDefaultWorkspace ? undefined : protectedApp} />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
  return { ...rendered, client };
}

const LogoutProbe: React.FC = () => {
  const { logout } = useAuth();
  return <button onClick={() => void logout().catch(() => undefined)}>Logout</button>;
};

const RecheckProbe: React.FC = () => {
  const client = useQueryClient();
  return <button onClick={() => void client.invalidateQueries({ queryKey: ['auth', 'me'] })}>Recheck session</button>;
};

const StatefulScopeProbe: React.FC = () => {
  const [value, setValue] = React.useState('fresh page state');
  return (
    <div>
      <span>{value}</span>
      <button onClick={() => setValue('stale page state')}>Change local page state</button>
      <RecheckProbe />
    </div>
  );
};

afterEach(() => {
  vi.clearAllMocks();
});

describe('authentication route gate', () => {
  it('keeps the app closed until /auth/me restores a valid session', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user);

    renderRoutes('/');

    expect(await screen.findByText('Protected application')).toBeInTheDocument();
    expect(authApi.me).toHaveBeenCalledTimes(1);
    expect(authApi.me).toHaveBeenCalledWith(expect.any(AbortSignal));
  });

  it('loads the Company module-state contract when the default protected workspace mounts', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user);
    const moduleState = { company_id: user.companies[0].id, modules: [] };
    vi.mocked(companyModuleStates).mockResolvedValue(moduleState);

    const { client } = renderRoutes('/', undefined, true);

    expect(await screen.findByText('Workspace surface')).toBeInTheDocument();
    await waitFor(() => expect(companyModuleStates).toHaveBeenCalledWith(
      user.companies[0].id,
      expect.any(AbortSignal),
    ));
    await waitFor(() => expect(client.getQueryData(
      queryKeys.companyModuleStates(user.id, user.companies[0].id),
    )).toEqual(moduleState));
  });

  it('redirects an anonymous user to Login and rejects an external return URL', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new ApiError({ message: 'No session', status: 401 }));

    renderRoutes('/private?next=https://attacker.example');

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByLabelText('Login ID')).toBeInTheDocument();
  });

  it('logs in, then renders the app only after the server identity loads', async () => {
    vi.mocked(authApi.me).mockRejectedValueOnce(new ApiError({ message: 'No session', status: 401 }))
      .mockResolvedValueOnce(user);
    vi.mocked(authApi.login).mockResolvedValue({ must_change_password: false });

    renderRoutes('/login');
    await screen.findByRole('heading', { name: 'Sign in' });
    fireEvent.change(screen.getByLabelText('Login ID'), { target: { value: 'accountant-1' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'temporary-secret' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByText('Protected application')).toBeInTheDocument();
    expect(authApi.login).toHaveBeenCalledWith('accountant-1', 'temporary-secret');
    expect(authApi.me).toHaveBeenCalledTimes(2);
  });

  it('forces the temporary-password route and opens the app only after /me clears the gate', async () => {
    vi.mocked(authApi.me).mockResolvedValueOnce({ ...user, must_change_password: true })
      .mockResolvedValueOnce(user);
    vi.mocked(authApi.changePassword).mockResolvedValue({ detail: 'Password changed' });

    renderRoutes('/');

    expect(await screen.findByRole('heading', { name: 'Change your temporary password' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'temporary-secret' } });
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'new-long-password' } });
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'new-long-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Update password' }));

    expect(await screen.findByText('Protected application')).toBeInTheDocument();
    expect(authApi.changePassword).toHaveBeenCalledWith('temporary-secret', 'new-long-password', 'new-long-password');
  });

  it('clears authenticated UI when a protected request reports session expiry', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user);

    renderRoutes('/');
    expect(await screen.findByText('Protected application')).toBeInTheDocument();
    window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument());
    expect(authApi.me).toHaveBeenCalledTimes(1);
  });

  it('purges user-scoped query data when a session recheck returns 401', async () => {
    vi.mocked(authApi.me)
      .mockResolvedValueOnce(user)
      .mockRejectedValueOnce(new ApiError({ message: 'Session expired', status: 401 }));

    const { client } = renderRoutes('/', <RecheckProbe />);
    const privateKey = ['branches', user.id, user.companies[0].id, 1] as const;
    client.setQueryData(privateKey, { results: ['private-context'] });

    fireEvent.click(await screen.findByRole('button', { name: 'Recheck session' }));

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(client.getQueryData(privateKey)).toBeUndefined();
  });

  it('purges scoped query data when the same user receives a changed Company role context', async () => {
    vi.mocked(authApi.me)
      .mockResolvedValueOnce(user)
      .mockResolvedValueOnce({
        ...user,
        roles: ['investor'],
        companies: [{ ...user.companies[0], roles: ['investor'], company_wide_roles: ['investor'] }],
      });

    const { client } = renderRoutes('/', <RecheckProbe />);
    const privateKey = ['branches', user.id, user.companies[0].id, 1] as const;
    client.setQueryData(privateKey, { results: ['owner-context'] });

    fireEvent.click(await screen.findByRole('button', { name: 'Recheck session' }));

    await waitFor(() => expect(client.getQueryData(privateKey)).toBeUndefined());
    expect(await screen.findByRole('button', { name: 'Recheck session' })).toBeInTheDocument();
  });

  it('remounts role-sensitive UI when the server returns a changed authorization scope', async () => {
    vi.mocked(authApi.me)
      .mockResolvedValueOnce(user)
      .mockResolvedValueOnce({
        ...user,
        roles: ['investor'],
        companies: [{ ...user.companies[0], roles: ['investor'], company_wide_roles: ['investor'] }],
      });

    renderRoutes('/', <StatefulScopeProbe />);
    fireEvent.click(await screen.findByRole('button', { name: 'Change local page state' }));
    expect(screen.getByText('stale page state')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Recheck session' }));

    expect(await screen.findByText('fresh page state')).toBeInTheDocument();
  });

  it('fails closed when a Company account has missing or ambiguous Company context', async () => {
    vi.mocked(authApi.me).mockResolvedValue({
      ...user,
      companies: [user.companies[0], { ...user.companies[0], id: 'be2c362c-ef07-468f-9b1f-8d6b13a2c318' }],
      tenant_ids: [user.tenant_ids[0], 'be2c362c-ef07-468f-9b1f-8d6b13a2c318'],
    });

    renderRoutes('/');

    expect(await screen.findByRole('heading', { name: 'Session check unavailable' })).toBeInTheDocument();
    expect(screen.getByText(/Company access could not be verified/i)).toBeInTheDocument();
    expect(screen.queryByText('Protected application')).not.toBeInTheDocument();
  });

  it('does not select a Company or request Branches from truncated Company context', async () => {
    vi.mocked(authApi.me).mockResolvedValue({
      ...user,
      company_context_truncated: true,
    });

    renderRoutes('/');

    expect(await screen.findByRole('heading', { name: 'Session check unavailable' })).toBeInTheDocument();
    expect(authApi.branches).not.toHaveBeenCalled();
    expect(screen.queryByText('Protected application')).not.toBeInTheDocument();
  });

  it('purges user-scoped query data after confirmed logout', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user);
    vi.mocked(authApi.logout).mockResolvedValue({ detail: 'Signed out' });

    const { client } = renderRoutes('/', <LogoutProbe />);
    const privateKey = ['branches', user.id, user.companies[0].id, 1] as const;
    const cancelQueries = vi.spyOn(client, 'cancelQueries');
    client.setQueryData(privateKey, { results: ['private-context'] });
    fireEvent.click(await screen.findByRole('button', { name: 'Logout' }));

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(authApi.logout).toHaveBeenCalledTimes(1);
    expect(cancelQueries).toHaveBeenCalled();
    expect(client.getQueryData(privateKey)).toBeUndefined();
  });

  it('aborts an in-flight scoped request before clearing its cache on logout', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user);
    vi.mocked(authApi.logout).mockResolvedValue({ detail: 'Signed out' });
    let requestSignal: AbortSignal | undefined;
    vi.mocked(authApi.branches).mockImplementation((_companyId, _page, signal) => {
      requestSignal = signal;
      return new Promise((_resolve, reject) => {
        signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true });
      });
    });

    const { client } = renderRoutes('/', <LogoutProbe />);
    const privateKey = ['branches', user.id, user.companies[0].id, 1] as const;
    const pending = client.fetchQuery({
      queryKey: privateKey,
      queryFn: ({ signal }) => authApi.branches(user.companies[0].id, 1, signal),
      retry: false,
    });
    void pending.catch(() => undefined);

    await waitFor(() => expect(requestSignal).toBeInstanceOf(AbortSignal));
    fireEvent.click(await screen.findByRole('button', { name: 'Logout' }));

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(requestSignal?.aborted).toBe(true);
    expect(client.getQueryData(privateKey)).toBeUndefined();
  });

  it('rechecks the server identity after an unconfirmed logout instead of claiming logout succeeded', async () => {
    vi.mocked(authApi.me).mockResolvedValue(user);
    vi.mocked(authApi.logout).mockRejectedValue(new ApiError({ message: 'Network unavailable', status: 0 }));

    renderRoutes('/', <LogoutProbe />);
    expect(await screen.findByRole('button', { name: 'Logout' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }));

    expect(await screen.findByRole('button', { name: 'Logout' })).toBeInTheDocument();
    expect(authApi.me).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole('heading', { name: 'Sign in' })).not.toBeInTheDocument();
  });
});
