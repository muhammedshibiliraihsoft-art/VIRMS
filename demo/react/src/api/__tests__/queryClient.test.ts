import { describe, expect, it } from 'vitest';
import { ApiError } from '../apiError';
import { createVirmsQueryClient } from '../queryClient';

describe('TanStack Query safety defaults', () => {
  it('retries safe-read transient failures once and respects Retry-After', () => {
    const client = createVirmsQueryClient();
    const retry = client.getDefaultOptions().queries?.retry;
    const delay = client.getDefaultOptions().queries?.retryDelay;
    expect(typeof retry).toBe('function');
    expect((retry as (count: number, error: unknown) => boolean)(0, new ApiError({
      message: 'Wait', status: 429, retryAfterMs: 3500,
    }))).toBe(true);
    expect((retry as (count: number, error: unknown) => boolean)(1, new ApiError({
      message: 'Wait', status: 429, retryAfterMs: 3500,
    }))).toBe(false);
    expect((delay as (count: number, error: unknown) => number)(0, new ApiError({
      message: 'Wait', status: 429, retryAfterMs: 3500,
    }))).toBe(3500);
    client.clear();
  });

  it('never retries mutations', () => {
    const client = createVirmsQueryClient();
    expect(client.getDefaultOptions().mutations?.retry).toBe(false);
    client.clear();
  });
});
