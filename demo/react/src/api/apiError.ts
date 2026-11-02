export type ApiFieldErrors = Record<string, string[]>;

export interface ApiErrorPayload {
  detail?: unknown;
  code?: unknown;
  request_id?: unknown;
  errors?: unknown;
  [key: string]: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly requestId: string | null;
  readonly retryAfterMs: number | null;
  readonly fieldErrors: ApiFieldErrors;

  constructor(input: {
    message: string;
    status: number;
    code?: string | null;
    requestId?: string | null;
    retryAfterMs?: number | null;
    fieldErrors?: ApiFieldErrors;
  }) {
    super(input.message);
    this.name = 'ApiError';
    this.status = input.status;
    this.code = input.code ?? null;
    this.requestId = input.requestId ?? null;
    this.retryAfterMs = input.retryAfterMs ?? null;
    this.fieldErrors = input.fieldErrors ?? {};
  }
}

export function parseRetryAfter(value: string | null, now = Date.now()): number | null {
  if (!value) return null;
  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds >= 0) {
    return Math.ceil(seconds * 1000);
  }
  const date = Date.parse(value);
  return Number.isNaN(date) ? null : Math.max(0, date - now);
}

function safeMessage(status: number, payload: ApiErrorPayload): string {
  const detail = typeof payload.detail === 'string' ? payload.detail : null;
  if (status === 400) return detail || 'Please review the submitted information.';
  if (status === 401) return 'Authentication is required. Please sign in again.';
  if (status === 403) return 'You do not have permission to perform this action.';
  if (status === 404) return 'The requested item was not found.';
  if (status === 409) return detail || 'The request conflicts with the current state.';
  if (status === 429) return 'Too many requests. Wait before trying again.';
  if (status >= 500) return 'The service is temporarily unavailable.';
  return detail || 'The request could not be completed.';
}

function collectFieldErrors(payload: ApiErrorPayload): ApiFieldErrors {
  const result: ApiFieldErrors = {};
  const source = payload.errors;
  if (Array.isArray(source)) {
    const messages = source.filter((value): value is string => typeof value === 'string');
    if (messages.length) result.non_field_errors = messages;
  } else if (source && typeof source === 'object') {
    for (const [field, value] of Object.entries(source)) {
      const messages = Array.isArray(value) ? value : [value];
      const safeMessages = messages.filter((item): item is string => typeof item === 'string');
      if (safeMessages.length) result[field] = safeMessages;
    }
  }
  return result;
}

export function normalizeApiError(
  status: number,
  payload: ApiErrorPayload,
  headers: Headers,
  fallbackRequestId: string,
  now = Date.now()
): ApiError {
  return new ApiError({
    message: safeMessage(status, payload),
    status,
    code: typeof payload.code === 'string' ? payload.code : null,
    requestId: headers.get('X-Request-ID') ||
      (typeof payload.request_id === 'string' ? payload.request_id : fallbackRequestId),
    retryAfterMs: parseRetryAfter(headers.get('Retry-After'), now),
    fieldErrors: collectFieldErrors(payload),
  });
}
