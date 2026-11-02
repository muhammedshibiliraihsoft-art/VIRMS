import { ApiError, ApiErrorPayload, normalizeApiError } from './apiError';

export const SESSION_EXPIRED_EVENT = 'virms:session-expired';

export type ApiMethod = 'GET' | 'POST';

export interface ApiRequestOptions {
  method?: ApiMethod;
  body?: unknown;
  headers?: HeadersInit;
  csrf?: boolean;
  signal?: AbortSignal;
}

function newRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const value = Math.floor(Math.random() * 16);
    return (char === 'x' ? value : (value & 0x3) | 0x8).toString(16);
  });
}

function cookieValue(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const prefix = `${name}=`;
  const item = document.cookie.split(';').map((part) => part.trim()).find((part) => part.startsWith(prefix));
  if (!item) return null;
  try {
    return decodeURIComponent(item.slice(prefix.length));
  } catch {
    return item.slice(prefix.length);
  }
}

async function readJson(response: Response): Promise<unknown> {
  if (response.status === 204) return null;
  const contentType = response.headers.get('Content-Type') || '';
  if (!contentType.toLowerCase().includes('application/json')) return null;
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function csrfToken(): Promise<string> {
  const existing = cookieValue('csrftoken');
  if (existing) return existing;
  await requestApi('auth/csrf/', { method: 'GET', csrf: false });
  const token = cookieValue('csrftoken');
  if (!token) {
    throw new ApiError({
      message: 'The security token could not be initialized. Reload and try again.',
      status: 0,
      code: 'csrf_token_missing',
    });
  }
  return token;
}

function dispatchSessionExpired(requestId: string): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT, { detail: { requestId } }));
  }
}

export async function requestApi<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const cleanPath = path.replace(/^\/+/, '');
  if (!cleanPath || cleanPath.startsWith('http:') || cleanPath.startsWith('https:')) {
    throw new ApiError({ message: 'Invalid API path.', status: 0, code: 'invalid_api_path' });
  }

  const method = options.method ?? 'GET';
  const requestId = newRequestId();
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  headers.set('X-Request-ID', requestId);

  let body: BodyInit | undefined;
  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(options.body);
  }

  if (method !== 'GET' && options.csrf !== false) {
    headers.set('X-CSRFToken', await csrfToken());
  }

  let response: Response;
  try {
    response = await fetch(`/api/v1/${cleanPath}`, {
      method,
      credentials: 'include',
      cache: 'no-store',
      headers,
      body,
      signal: options.signal,
    });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError({
      message: 'The server could not be reached. Check the connection and try again.',
      status: 0,
      code: 'network_error',
      requestId,
    });
  }

  const payload = await readJson(response);
  if (!response.ok) {
    const errorPayload: ApiErrorPayload =
      payload && typeof payload === 'object' && !Array.isArray(payload)
        ? payload as ApiErrorPayload
        : {};
    const error = normalizeApiError(
      response.status,
      errorPayload,
      response.headers,
      requestId
    );
    if (
      response.status === 401 &&
      cleanPath !== 'auth/login/' &&
      cleanPath !== 'auth/csrf/' &&
      cleanPath !== 'auth/me/'
    ) {
      dispatchSessionExpired(error.requestId || requestId);
    }
    throw error;
  }

  if (response.status === 204) return undefined as T;
  if (payload === null) {
    throw new ApiError({
      message: 'The server returned an unreadable response.',
      status: 0,
      code: 'invalid_response',
      requestId: response.headers.get('X-Request-ID') || requestId,
    });
  }
  return payload as T;
}
