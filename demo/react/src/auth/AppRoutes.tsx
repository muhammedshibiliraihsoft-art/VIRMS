import React, { useEffect } from 'react';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import App from '../App';
import { useCompanyModuleStates } from '../api/queries';
import { AuthLoadingPage, AuthUnavailablePage, FirstPasswordPage, LoginPage } from './AuthPages';
import { authScopeFingerprint, AuthProvider, isPlatformUser, useAuth } from './AuthContext';

export const AppRoutes: React.FC<{ protectedApp?: React.ReactNode }> = ({ protectedApp }) => {
  const auth = useAuth();
  const navigate = useNavigate();

  if (auth.status === 'loading') return <AuthLoadingPage />;
  if (auth.status === 'error') return <AuthUnavailablePage />;
  if (auth.status === 'authenticated' && isPlatformUser(auth.user)) return <PlatformAdminRedirect />;

  const handleLogout = async () => {
    await auth.logout();
    navigate('/login', { replace: true });
  };

  const protectedContent = protectedApp ?? (
    <>
      <WorkspaceModuleStateBootstrap />
      <App
        onLogout={handleLogout}
        loginId={auth.user?.login_id}
        companyName={auth.currentCompany?.name}
        companyWideRoles={auth.currentCompany?.company_wide_roles}
        branchContexts={auth.currentCompany?.branches}
        branchesTruncated={auth.currentCompany?.branches_truncated}
      />
    </>
  );
  const scopedProtectedContent = (
    <React.Fragment key={auth.user ? authScopeFingerprint(auth.user) : 'missing-auth-context'}>
      {protectedContent}
    </React.Fragment>
  );

  return (
    <Routes>
      <Route
        path="/login"
        element={
          auth.status === 'anonymous'
            ? <LoginPage />
            : <Navigate to={auth.status === 'password_change_required' ? '/password/change' : '/'} replace />
        }
      />
      <Route
        path="/password/change"
        element={
          auth.status === 'anonymous'
            ? <Navigate to="/login" replace />
            : auth.status === 'password_change_required'
              ? <FirstPasswordPage />
              : <Navigate to="/" replace />
        }
      />
      <Route
        path="*"
        element={
          auth.status === 'anonymous'
            ? <Navigate to="/login" replace />
            : auth.status === 'password_change_required'
              ? <Navigate to="/password/change" replace />
              : scopedProtectedContent
        }
      />
    </Routes>
  );
};

const WorkspaceModuleStateBootstrap: React.FC = () => {
  useCompanyModuleStates();
  return null;
};

export const AuthenticatedApplication: React.FC<{ protectedApp?: React.ReactNode }> = ({ protectedApp }) => (
  <AuthProvider>
    <AppRoutes protectedApp={protectedApp} />
  </AuthProvider>
);

const PlatformAdminRedirect: React.FC = () => {
  useEffect(() => {
    window.location.replace('/admin/');
  }, []);
  return <AuthLoadingPage />;
};
