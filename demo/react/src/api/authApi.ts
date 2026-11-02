import { requestApi } from './client';
import { AuthMe, BranchPage, LoginResponse, parseAuthMe, parseBranchPage } from './types';

export const authApi = {
  async me(signal?: AbortSignal): Promise<AuthMe> {
    return parseAuthMe(await requestApi<unknown>('auth/me/', { signal }));
  },
  async login(loginId: string, password: string): Promise<LoginResponse> {
    const value = await requestApi<unknown>('auth/login/', {
      method: 'POST',
      body: { login_id: loginId, password },
    });
    if (!value || typeof value !== 'object' || typeof (value as Record<string, unknown>).must_change_password !== 'boolean') {
      throw new Error('Invalid login response.');
    }
    return value as LoginResponse;
  },
  logout(): Promise<{ detail: string }> {
    return requestApi<{ detail: string }>('auth/logout/', { method: 'POST', body: {} });
  },
  changePassword(currentPassword: string, newPassword: string, confirmPassword: string): Promise<{ detail: string }> {
    return requestApi<{ detail: string }>('auth/password/change/', {
      method: 'POST',
      body: {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      },
    });
  },
  async branches(companyId: string, page = 1, signal?: AbortSignal): Promise<BranchPage> {
    const query = new URLSearchParams({ page: String(page) });
    return parseBranchPage(
      await requestApi<unknown>(`tenants/${encodeURIComponent(companyId)}/branches/?${query.toString()}`, { signal })
    );
  },
};
