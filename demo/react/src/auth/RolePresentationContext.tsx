import React, { createContext, useContext } from 'react';
import { canPresentBusinessWriteActions } from '../data/roleNavigation';

const BusinessWritePresentationContext = createContext(false);

export const RolePresentationProvider: React.FC<React.PropsWithChildren<{
  companyWideRoles?: readonly string[];
}>> = ({ companyWideRoles, children }) => (
  <BusinessWritePresentationContext.Provider value={canPresentBusinessWriteActions(companyWideRoles)}>
    {children}
  </BusinessWritePresentationContext.Provider>
);

export function useCanPresentBusinessWriteActions(): boolean {
  return useContext(BusinessWritePresentationContext);
}
