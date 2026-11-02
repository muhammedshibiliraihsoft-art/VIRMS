import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { ApiError, normalizeApiError } from '../../api/apiError';
import { AuthContextValue, useAuth } from '../AuthContext';
import { LoginPage } from '../AuthPages';

vi.mock('../AuthContext', () => ({ useAuth: vi.fn() }));

const errorCases = [
  {
    label: '400 validation',
    error: normalizeApiError(400, { errors: { login_id: ['Enter a valid Login ID.'] } }, new Headers(), 'request-400'),
    expected: 'Enter a valid Login ID.',
  },
  {
    label: '401 authentication',
    error: normalizeApiError(401, { detail: 'internal credential detail' }, new Headers(), 'request-401'),
    expected: 'Login ID or password is incorrect.',
  },
  {
    label: '403 permission',
    error: normalizeApiError(403, { detail: 'private permission detail' }, new Headers(), 'request-403'),
    expected: 'You do not have permission to perform this action.',
  },
  {
    label: '404 missing resource',
    error: normalizeApiError(404, { detail: 'private resource detail' }, new Headers(), 'request-404'),
    expected: 'The requested item was not found.',
  },
  {
    label: '409 conflict',
    error: normalizeApiError(409, { detail: 'The account changed. Reload and try again.' }, new Headers(), 'request-409'),
    expected: 'The account changed. Reload and try again.',
  },
  {
    label: '429 rate limit',
    error: normalizeApiError(429, { detail: 'private throttle detail' }, new Headers(), 'request-429'),
    expected: 'Too many requests. Wait before trying again.',
  },
  {
    label: '500 server failure',
    error: normalizeApiError(500, { detail: 'password hash stack trace' }, new Headers(), 'request-500'),
    expected: 'The service is temporarily unavailable.',
  },
  {
    label: '503 service unavailable',
    error: normalizeApiError(503, { detail: 'private service detail' }, new Headers(), 'request-503'),
    expected: 'The service is temporarily unavailable.',
  },
  {
    label: 'network failure',
    error: new ApiError({
      message: 'The server could not be reached. Check the connection and try again.',
      status: 0,
      code: 'network_error',
      requestId: 'request-network',
    }),
    expected: 'The server could not be reached. Check the connection and try again.',
  },
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('LoginPage API error feedback', () => {
  it.each(errorCases)('renders $label errors as accessible, safe feedback', async ({ error, expected }) => {
    const login = vi.fn().mockRejectedValue(error);
    vi.mocked(useAuth).mockReturnValue({ login } as unknown as AuthContextValue);

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText('Login ID'), { target: { value: 'test-account' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'test-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(expected);
    expect(alert).not.toHaveTextContent(/stack trace|private .* detail|internal credential/i);
    expect(screen.getByLabelText('Login ID')).toHaveAttribute('aria-describedby', 'login-error');
    expect(screen.getByLabelText('Password')).toHaveAttribute('aria-describedby', 'login-error');
  });

  it('uses a generic alert for an unrecognized error without exposing its message', async () => {
    const login = vi.fn().mockRejectedValue(new Error('database password leaked'));
    vi.mocked(useAuth).mockReturnValue({ login } as unknown as AuthContextValue);

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText('Login ID'), { target: { value: 'test-account' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'test-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('The request could not be completed. Try again.');
    expect(alert).not.toHaveTextContent('database password leaked');
  });
});
