import { QueryClient } from '@tanstack/react-query';
import { ApiError } from './apiError';

function shouldRetryRead(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) return false;
  if (!(error instanceof ApiError)) return false;
  if (error.status === 0) return error.code === 'network_error';
  return [429, 500, 502, 503, 504].includes(error.status);
}

function retryDelay(failureCount: number, error: unknown): number {
  if (error instanceof ApiError && error.retryAfterMs !== null) {
    return error.retryAfterMs;
  }
  return Math.min(1000 * 2 ** failureCount, 10_000);
}

export function createVirmsQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        retry: shouldRetryRead,
        retryDelay,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}
