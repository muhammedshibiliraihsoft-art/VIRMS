import React, { FormEvent, useState } from 'react';
import { ApiError } from '../api/apiError';
import { useAuth } from './AuthContext';

function authErrorMessage(error: unknown, login = false): string {
  if (error instanceof Error && error.message === 'A single authorized Company context could not be verified.') {
    return 'Company access could not be verified. Contact your administrator before continuing.';
  }
  if (error instanceof ApiError) {
    if (login && error.status === 401) return 'Login ID or password is incorrect.';
    const fieldMessages = Object.values(error.fieldErrors).flat();
    return fieldMessages[0] || error.message;
  }
  return 'The request could not be completed. Try again.';
}

export const AuthLoadingPage: React.FC = () => (
  <main className="min-h-screen flex items-center justify-center bg-[var(--theme-bg-app)] p-4" role="status" aria-live="polite">
    <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-5 py-4 text-sm font-medium text-gray-700 shadow-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-gray-200">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-[var(--theme-primary)]" aria-hidden="true" />
      Checking your session…
    </div>
  </main>
);

export const AuthUnavailablePage: React.FC = () => {
  const { error, retryBootstrap } = useAuth();
  const [retrying, setRetrying] = useState(false);
  const [message, setMessage] = useState('');
  const displayError = message || (error ? authErrorMessage(error) : '');

  const handleRetry = async () => {
    setRetrying(true);
    setMessage('');
    try {
      await retryBootstrap();
    } catch (retryError) {
      setMessage(authErrorMessage(retryError));
    } finally {
      setRetrying(false);
    }
  };

  return (
    <AuthFrame>
      <h1 className="text-xl font-bold text-gray-950 dark:text-white">Session check unavailable</h1>
      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
        VIRMS could not verify your session. No protected workspace data was opened.
      </p>
      {displayError && <p className="mt-3 text-sm text-rose-700 dark:text-rose-300" role="alert">{displayError}</p>}
      <button className={primaryButtonClass} type="button" onClick={handleRetry} disabled={retrying}>
        {retrying ? 'Checking…' : 'Retry'}
      </button>
    </AuthFrame>
  );
};

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError('');
    try {
      await login(loginId, password);
      setPassword('');
    } catch (loginError) {
      setError(authErrorMessage(loginError, true));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthFrame>
      <div className="mb-5 flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--theme-primary)] text-sm font-extrabold text-white">V</span>
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--theme-primary)]">VIRMS</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Operations</p>
        </div>
      </div>
      <h1 className="text-xl font-bold text-gray-950 dark:text-white">Sign in</h1>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">Use your Login ID and password.</p>
      <form className="mt-5 space-y-4" onSubmit={handleSubmit} noValidate>
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-gray-800 dark:text-gray-200" htmlFor="login-id">Login ID</label>
          <input
            id="login-id"
            name="login_id"
            type="text"
            autoComplete="username"
            required
            value={loginId}
            onChange={(event) => setLoginId(event.target.value)}
            className={inputClass}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? 'login-error' : undefined}
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-gray-800 dark:text-gray-200" htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className={inputClass}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? 'login-error' : undefined}
          />
        </div>
        {error && <p id="login-error" className="text-sm text-rose-700 dark:text-rose-300" role="alert">{error}</p>}
        <button className={primaryButtonClass} type="submit" disabled={submitting || !loginId || !password}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </AuthFrame>
  );
};

export const FirstPasswordPage: React.FC = () => {
  const { changePassword } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;
    if (Array.from(newPassword).length < 6) {
      setError('Password must contain at least 6 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('The new passwords do not match.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await changePassword(currentPassword, newPassword, confirmPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (changeError) {
      setError(authErrorMessage(changeError));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthFrame>
      <p className="text-xs font-bold uppercase tracking-widest text-[var(--theme-primary)]">VIRMS</p>
      <h1 className="mt-2 text-xl font-bold text-gray-950 dark:text-white">Change your temporary password</h1>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">Use at least 6 characters. Numbers, letters, and symbols are allowed.</p>
      <form className="mt-5 space-y-4" onSubmit={handleSubmit} noValidate>
        <PasswordField id="current-password" label="Current password" value={currentPassword} onChange={setCurrentPassword} autoComplete="current-password" errorId={error ? 'password-change-error' : undefined} />
        <PasswordField id="new-password" label="New password" value={newPassword} onChange={setNewPassword} autoComplete="new-password" errorId={error ? 'password-change-error' : undefined} ariaInvalid={error === 'The new passwords do not match.'} />
        <PasswordField id="confirm-password" label="Confirm new password" value={confirmPassword} onChange={setConfirmPassword} autoComplete="new-password" errorId={error ? 'password-change-error' : undefined} ariaInvalid={error === 'The new passwords do not match.'} />
        {error && <p id="password-change-error" className="text-sm text-rose-700 dark:text-rose-300" role="alert">{error}</p>}
        <button className={primaryButtonClass} type="submit" disabled={submitting || !currentPassword || !newPassword || !confirmPassword}>
          {submitting ? 'Updating…' : 'Update password'}
        </button>
      </form>
    </AuthFrame>
  );
};

const AuthFrame: React.FC<React.PropsWithChildren> = ({ children }) => (
  <main className="min-h-screen flex items-center justify-center bg-[var(--theme-bg-app)] p-4">
    <section className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900" aria-label="VIRMS authentication">
      {children}
    </section>
  </main>
);

const PasswordField: React.FC<{
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete: string;
  errorId?: string;
  ariaInvalid?: boolean;
}> = ({ id, label, value, onChange, autoComplete, errorId, ariaInvalid = false }) => (
  <div>
    <label className="mb-1.5 block text-sm font-semibold text-gray-800 dark:text-gray-200" htmlFor={id}>{label}</label>
    <input
      id={id}
      name={id}
      type="password"
      autoComplete={autoComplete}
      required
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={inputClass}
      aria-invalid={ariaInvalid}
      aria-describedby={errorId}
    />
  </div>
);

const inputClass = 'h-11 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm text-gray-900 outline-none transition focus:border-[var(--theme-primary)] focus:ring-2 focus:ring-[var(--theme-primary-soft)] dark:border-zinc-700 dark:bg-zinc-800 dark:text-white';
const primaryButtonClass = 'mt-2 inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[var(--theme-primary)] px-4 py-2 text-sm font-bold text-white transition hover:bg-[var(--theme-primary-hover)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60';
