import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { AuthenticatedApplication } from './auth/AppRoutes';
import { createVirmsQueryClient } from './api/queryClient';
import './index.css';

const queryClient = createVirmsQueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthenticatedApplication />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
