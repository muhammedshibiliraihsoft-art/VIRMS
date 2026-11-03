import { requestApi } from './client';
import { CompanyModuleStatesResponse, parseCompanyModuleStates } from './types';

export async function companyModuleStates(
  companyId: string,
  signal?: AbortSignal,
): Promise<CompanyModuleStatesResponse> {
  const response = await requestApi<unknown>(
    `tenants/${encodeURIComponent(companyId)}/module-state/`,
    { signal },
  );
  const contract = parseCompanyModuleStates(response);
  if (contract.company_id !== companyId) {
    throw new Error('Invalid Company module-state response.');
  }
  return contract;
}
