import js from '@eslint/js';
import reactHooks from 'eslint-plugin-react-hooks';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';

export default defineConfig({
  files: [
    'src/api/**/*.{ts,tsx}',
    'src/auth/**/*.{ts,tsx}',
    'src/main.tsx',
    'src/components/AppShell.tsx',
    'src/components/TopBar.tsx',
    'src/components/dashboard/DashboardHeader.tsx',
    'src/components/shared/Phase5WorkspaceView.tsx',
    'src/components/shared/__tests__/Phase5WorkspaceView.test.tsx',
    'src/components/shared/Garage*.tsx',
    'src/components/shared/LabourWorkspace.tsx',
    'src/components/shared/LabourPaymentCorrection.tsx',
    'src/components/shared/__tests__/Garage*.test.tsx',
    'src/components/shared/__tests__/LabourWorkspace.test.tsx',
    'src/components/shared/__tests__/LabourPaymentCorrection.test.tsx',
  ],
  extends: [js.configs.recommended, ...tseslint.configs.recommended],
  plugins: { 'react-hooks': reactHooks },
  rules: {
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
  },
});
