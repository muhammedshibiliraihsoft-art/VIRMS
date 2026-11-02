import { describe, expect, it } from 'vitest';
import { queryKeys } from '../queryKeys';

describe('scope-sensitive query keys', () => {
  it('includes user and Company UUIDs for Branch pages', () => {
    expect(queryKeys.branches('user-a', 'company-a', 1)).not.toEqual(queryKeys.branches('user-b', 'company-a', 1));
    expect(queryKeys.branches('user-a', 'company-a', 1)).not.toEqual(queryKeys.branches('user-a', 'company-b', 1));
    expect(queryKeys.branches('user-a', 'company-a', 1)).not.toEqual(queryKeys.branches('user-a', 'company-a', 2));
  });

  it('includes user, Company and Branch UUIDs for a Branch-specific key', () => {
    const key = queryKeys.branch('user-a', 'company-a', 'branch-a');

    expect(key).not.toEqual(queryKeys.branch('user-b', 'company-a', 'branch-a'));
    expect(key).not.toEqual(queryKeys.branch('user-a', 'company-b', 'branch-a'));
    expect(key).not.toEqual(queryKeys.branch('user-a', 'company-a', 'branch-b'));
  });
});
