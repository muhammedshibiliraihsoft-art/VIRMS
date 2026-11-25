import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { PrimaryBalanceCard } from '../PrimaryBalanceCard';
import { MetricGrid } from '../MetricCard';
import { PerformanceChart } from '../PerformanceChart';
import { InvestorUtilizationCard } from '../InvestorUtilizationCard';
import { RecentActivityTable } from '../RecentActivityTable';
import { ActivityItem } from '../../types';
import { useAuth } from '../../auth/AuthContext';
import { hasCompanyBranchReadRole, useCompanyModuleStates } from '../../api/queries';
import { phase5Api } from '../../api/phase5Api';
import { garageApi } from '../../api/garageApi';
import { queryKeys } from '../../api/queryKeys';
import { useAccountingEvents, useAccountingMonthlyTrend } from '../../api/accountingQueries';
import { accountingAccounts } from '../../api/accountingApi';

interface DashboardOverviewViewProps {
  onRecordReceipt: () => void;
  onNewSale: () => void;
  onSelectActivity: (item: ActivityItem) => void;
}

export const DashboardOverviewView: React.FC<DashboardOverviewViewProps> = ({
  onRecordReceipt,
  onNewSale,
  onSelectActivity,
}) => {
  const { status, user, currentCompany } = useAuth();
  const moduleStates = useCompanyModuleStates();
  const garageEnabled = moduleStates.isSuccess && moduleStates.data.modules.some((row) => row.code === 'garage' && row.state === 'enabled');
  const vehicleEnabled = moduleStates.isSuccess && moduleStates.data.modules.some((row) => row.code === 'vehicle_management' && row.state === 'enabled');
  const investmentEnabled = moduleStates.isSuccess && moduleStates.data.modules.some((row) => row.code === 'investment' && row.state === 'enabled');
  const canReadCompanyData = status === 'authenticated' && Boolean(currentCompany) && hasCompanyBranchReadRole(user);
  const companyId = currentCompany?.id;
  const userId = user?.id;
  const hasCompanyWideAccountingRole = Boolean(currentCompany?.company_wide_roles.some((role) => ['owner', 'accountant'].includes(role)));
  const soleAuthorizedBranchId = currentCompany && !currentCompany.branches_truncated && currentCompany.branches.length === 1
    ? currentCompany.branches[0].id
    : undefined;
  const canReadAnnualAccountingResult = hasCompanyWideAccountingRole || Boolean(soleAuthorizedBranchId);

  const vehicleSummaryQuery = useQuery({
    queryKey: userId && companyId ? ['companies', userId, companyId, 'vehicle-management', 'operational-summary'] : ['dashboard', 'vehicles', 'unavailable'],
    queryFn: ({ signal }) => {
      if (!companyId) throw new Error('A single authorized Company context is required.');
      return phase5Api.operationalSummary(companyId, {}, signal);
    },
    enabled: canReadCompanyData && vehicleEnabled,
    retry: false,
  });
  const garageJobsQuery = useQuery({
    queryKey: userId && companyId ? ['garage', userId, companyId, 'jobs', 'dashboard-summary'] : ['dashboard', 'garage-jobs', 'unavailable'],
    queryFn: ({ signal }) => {
      if (!companyId) throw new Error('A single authorized Company context is required.');
      return garageApi.jobSummary(companyId, undefined, signal);
    },
    enabled: canReadCompanyData && garageEnabled,
    retry: false,
  });
  const fundSummaryQuery = useQuery({
    queryKey: userId && companyId ? queryKeys.phase5.fundSummary(userId, companyId) : ['dashboard', 'fund-summary', 'unavailable'],
    queryFn: ({ signal }) => {
      if (!companyId) throw new Error('A single authorized Company context is required.');
      return phase5Api.fundSummary(companyId, {}, signal);
    },
    enabled: canReadCompanyData && investmentEnabled,
    retry: false,
  });
  const accountingTrendQuery = useAccountingMonthlyTrend({
    branchId: hasCompanyWideAccountingRole ? undefined : soleAuthorizedBranchId,
    enabled: canReadAnnualAccountingResult,
  });
  const accountsQuery = useQuery({
    queryKey: userId && companyId ? queryKeys.accountingAccounts(userId, companyId) : ['dashboard', 'cash-bank-accounts', 'unavailable'],
    queryFn: ({ signal }) => {
      if (!companyId) throw new Error('A single authorized Company context is required.');
      return accountingAccounts(companyId, signal);
    },
    enabled: canReadAnnualAccountingResult,
    retry: false,
  });
  const accountingEventsQuery = useAccountingEvents({ page: 1 });
  const fundPosition = fundSummaryQuery.data ? {
    used: Number(fundSummaryQuery.data.used_total),
    available: Number(fundSummaryQuery.data.available_amount),
    reserved: Number(fundSummaryQuery.data.reserved_amount),
  } : undefined;

  const activities = (accountingEventsQuery.data?.results ?? []).map((event): ActivityItem => ({
    id: event.id,
    code: event.source_reference || '—',
    title: event.event_type.replaceAll('_', ' '),
    subtitle: event.description || event.branch_name || 'Accounting event',
    amount: Number(event.amount) * event.effect_sign,
    status: event.reversal_of_id ? 'Reversal' : event.replaces_event_id ? 'Correction' : 'Recorded',
    statusVariant: event.reversal_of_id ? 'warning' : 'info',
    date: event.effective_at,
    type: 'accounting',
  }));

  return (
    <div className="space-y-3 sm:space-y-3.5 animate-in fade-in duration-150">
      {/* Top Row: Primary Balance + Top Metrics + Income Chart (Image 1 Exact Composition) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-stretch">
        {/* Top Left: Primary Balance & Quick Actions (col-span-3) */}
        <div className="lg:col-span-3 min-w-0 flex flex-col">
          <PrimaryBalanceCard
            accounts={accountsQuery.data}
            isLoading={accountsQuery.isLoading}
            hasError={accountsQuery.isError || (!accountsQuery.data && !accountsQuery.isLoading)}
            onRecordReceipt={onRecordReceipt}
            onNewSale={onNewSale}
          />
        </div>

        {/* Top Middle: 4 Operational Metrics (col-span-4) */}
        <div className="lg:col-span-4 min-w-0 flex flex-col">
          <MetricGrid
            vehicleCount={vehicleSummaryQuery.data?.vehicle_count ?? null}
            soldVehicleCount={vehicleSummaryQuery.data?.sold_vehicle_count ?? null}
            buyerReceivable={vehicleSummaryQuery.data ? Number(vehicleSummaryQuery.data.buyer_receivable) : null}
            openJobsCount={garageJobsQuery.data?.open_jobs ?? null}
            vehiclesLoading={moduleStates.isLoading || vehicleSummaryQuery.isLoading}
            vehiclesError={!vehicleEnabled || vehicleSummaryQuery.isError || (!vehicleSummaryQuery.data && !vehicleSummaryQuery.isLoading)}
            garageLoading={moduleStates.isLoading || garageJobsQuery.isLoading}
            garageError={!garageEnabled || garageJobsQuery.isError || (!garageJobsQuery.data && !garageJobsQuery.isLoading)}
          />
        </div>

        {/* Top Right: Performance Chart (col-span-5) */}
        <div className="lg:col-span-5 min-w-0 flex flex-col">
          <PerformanceChart
            points={accountingTrendQuery.isError ? null : accountingTrendQuery.data?.monthly_trend.map((point) => ({
              label: point.label,
              income: Number(point.income_amount),
              expense: Number(point.expense_amount),
            })) ?? null}
            isLoading={accountingTrendQuery.isLoading}
            hasError={accountingTrendQuery.isError || (!accountingTrendQuery.data && !accountingTrendQuery.isLoading)}
          />
        </div>
      </div>

      {/* Preserve the reference Dashboard lower row: fund position beside activity. */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-start">
        <div className="lg:col-span-3 min-w-0">
          <InvestorUtilizationCard
            totalUsed={fundPosition?.used}
            availableAmount={fundPosition?.available}
            reservedAmount={fundPosition?.reserved}
            isLoading={moduleStates.isLoading || fundSummaryQuery.isLoading}
            hasError={!investmentEnabled || fundSummaryQuery.isError}
          />
        </div>
        <div className="lg:col-span-9 min-w-0">
          <RecentActivityTable
            activities={activities}
            onSelectActivity={onSelectActivity}
            isLoading={accountingEventsQuery.isLoading}
            hasError={accountingEventsQuery.isError}
          />
        </div>
      </div>
    </div>
  );
};

export default DashboardOverviewView;
