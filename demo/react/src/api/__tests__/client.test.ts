import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, normalizeApiError, parseRetryAfter } from '../apiError';
import { requestApi, SESSION_EXPIRED_EVENT } from '../client';

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });

async function expectApiError(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) return error;
    throw error;
  }
  throw new Error('Expected request to fail.');
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  document.cookie = 'csrftoken=; Max-Age=0; path=/';
});

describe('requestApi', () => {
  it('sends same-origin GET requests with cookies and correlation IDs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(json({ id: 'ok' }, 200, { 'X-Request-ID': 'server-id' }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(requestApi<{ id: string }>('auth/me/')).resolves.toEqual({ id: 'ok' });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/v1/auth/me/');
    expect(init.credentials).toBe('include');
    expect(init.cache).toBe('no-store');
    expect(new Headers(init.headers).get('Accept')).toBe('application/json');
    expect(new Headers(init.headers).get('X-Request-ID')).toMatch(/^[0-9a-f-]{36}$/i);
  });

  it('forwards TanStack cancellation signals to the underlying fetch', async () => {
    const fetchMock = vi.fn().mockResolvedValue(json({ id: 'ok' }));
    vi.stubGlobal('fetch', fetchMock);
    const signal = new AbortController().signal;

    await requestApi('auth/me/', { signal });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.signal).toBe(signal);
  });

  it('preserves an aborted fetch as cancellation instead of retryable network failure', async () => {
    const controller = new AbortController();
    const fetchMock = vi.fn((_url: string, init: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true });
    }));
    vi.stubGlobal('fetch', fetchMock);

    const request = requestApi('auth/me/', { signal: controller.signal });
    controller.abort();

    await expect(request).rejects.toMatchObject({ name: 'AbortError' });
  });

  it('fetches a CSRF cookie before unsafe requests and sends it in the header', async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string) => {
      if (url === '/api/v1/auth/csrf/') {
        document.cookie = 'csrftoken=csrf-token; path=/';
        return json({ detail: 'CSRF cookie set' });
      }
      return json({ must_change_password: false });
    });
    vi.stubGlobal('fetch', fetchMock);

    await requestApi('auth/login/', { method: 'POST', body: { login_id: 'test', password: 'secret' } });

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      '/api/v1/auth/csrf/',
      '/api/v1/auth/login/',
    ]);
    const [, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(new Headers(init.headers).get('X-CSRFToken')).toBe('csrf-token');
    expect(new Headers(init.headers).get('Content-Type')).toBe('application/json');
    expect(init.body).toBe(JSON.stringify({ login_id: 'test', password: 'secret' }));
  });

  it('normalizes validation errors, request IDs and Retry-After', async () => {
    document.cookie = 'csrftoken=csrf-token; path=/';
    const fetchMock = vi.fn().mockResolvedValue(
      json(
        { detail: 'Invalid request', errors: { login_id: ['Invalid format'] }, request_id: 'body-id' },
        429,
        { 'Retry-After': '3', 'X-Request-ID': 'header-id' }
      )
    );
    vi.stubGlobal('fetch', fetchMock);

    const error = await expectApiError(requestApi('auth/login/', { method: 'POST', body: {} }));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(429);
    expect(error.requestId).toBe('header-id');
    expect(error.retryAfterMs).toBe(3000);
    expect(error.fieldErrors).toEqual({ login_id: ['Invalid format'] });
  });

  it('does not expose server internals from 5xx responses', async () => {
    const fetchMock = vi.fn().mockResolvedValue(json({ detail: 'password hash stack trace' }, 500));
    vi.stubGlobal('fetch', fetchMock);

    const error = await expectApiError(requestApi('auth/me/'));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toBe('The service is temporarily unavailable.');
    expect(error.message).not.toContain('password hash');
  });

  it('emits a session-expired event for protected API 401s, but not login or me', async () => {
    document.cookie = 'csrftoken=csrf-token; path=/';
    const listener = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, listener);
    const fetchMock = vi.fn().mockResolvedValue(json({ detail: 'Authentication required' }, 401));
    vi.stubGlobal('fetch', fetchMock);

    await requestApi('tenants/company/branches/').catch(() => undefined);
    await requestApi('auth/me/').catch(() => undefined);
    await requestApi('auth/login/', { method: 'POST', body: {} }).catch(() => undefined);

    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(SESSION_EXPIRED_EVENT, listener);
  });

  it('normalizes network failures without leaking request data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('socket details')));

    const error = await expectApiError(requestApi('auth/me/'));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(0);
    expect(error.message).not.toContain('socket details');
    expect(error.requestId).toMatch(/^[0-9a-f-]{36}$/i);
  });
});

describe('error helpers', () => {
  it('parses Retry-After as seconds or an HTTP date', () => {
    expect(parseRetryAfter('2', 1_000)).toBe(2_000);
    expect(parseRetryAfter(new Date(5_000).toUTCString(), 1_000)).toBe(4_000);
    expect(parseRetryAfter('not-a-date', 1_000)).toBeNull();
  });

  it('prefers the server request ID over the client fallback', () => {
    const error = normalizeApiError(409, { detail: 'Conflict' }, new Headers({ 'X-Request-ID': 'server' }), 'client');
    expect(error.requestId).toBe('server');
  });
});
