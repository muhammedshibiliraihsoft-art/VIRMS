import { describe, expect, it } from 'vitest';
import { queryKeys } from '../queryKeys';

describe('scope-sensitive query keys', () => {
  it('includes user and Company UUIDs for Branch pages', () => {
    expect(queryKeys.branches('user-a', 'company-a', 1)).not.toEqual(queryKeys.branches('user-b', 'company-a', 1));
    expect(queryKeys.branches('user-a', 'company-a', 1)).not.toEqual(queryKeys.branches('user-a', 'company-b', 1));
    expect(queryKeys.branches('user-a', 'company-a', 1)).not.toEqual(queryKeys.branches('user-a', 'company-a', 2));
  });
});
