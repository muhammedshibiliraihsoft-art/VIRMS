import React from 'react';
import { PrimaryBalanceCard } from '../PrimaryBalanceCard';
import { MetricGrid } from '../MetricCard';
import { PerformanceChart } from '../PerformanceChart';
import { InvestorUtilizationCard } from '../InvestorUtilizationCard';
import { RecentActivityTable } from '../RecentActivityTable';
import { Investor, ActivityItem } from '../../types';

interface DashboardOverviewViewProps {
  totalBuyerReceivable: number;
  investors: Investor[];
  stockVehiclesCount: number;
  openJobsCount: number;
  inventoryStockValue: number;
  totalInvestorUsed: number;
  totalInvestorPrincipal: number;
  activities: ActivityItem[];
  onRecordReceipt: () => void;
  onNewSale: () => void;
  onSelectActivity: (item: ActivityItem) => void;
}

export const DashboardOverviewView: React.FC<DashboardOverviewViewProps> = ({
  totalBuyerReceivable,
  investors,
  stockVehiclesCount,
  openJobsCount,
  inventoryStockValue,
  totalInvestorUsed,
  totalInvestorPrincipal,
  activities,
  onRecordReceipt,
  onNewSale,
  onSelectActivity,
}) => {
  return (
    <div className="space-y-3 sm:space-y-3.5 animate-in fade-in duration-150">
      {/* Top Row: Primary Balance + Top Metrics + Income Chart (Image 1 Exact Composition) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-stretch">
        {/* Top Left: Primary Balance & Quick Actions (col-span-3) */}
        <div className="lg:col-span-3 min-w-0 flex flex-col">
          <PrimaryBalanceCard
            totalReceivable={totalBuyerReceivable}
            investors={investors}
            onRecordReceipt={onRecordReceipt}
            onNewSale={onNewSale}
          />
        </div>

        {/* Top Middle: 4 Operational Metrics (col-span-4) */}
        <div className="lg:col-span-4 min-w-0 flex flex-col">
          <MetricGrid
            stockVehiclesCount={stockVehiclesCount}
            openJobsCount={openJobsCount}
            totalReceivable={totalBuyerReceivable}
            inventoryStockValue={inventoryStockValue}
          />
        </div>

        {/* Top Right: Performance Chart (col-span-5) */}
        <div className="lg:col-span-5 min-w-0 flex flex-col">
          <PerformanceChart />
        </div>
      </div>

      {/* Bottom Row: Spending Limit & Recent Activities Table (Image 1 Exact Composition) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-start">
        {/* Bottom Left: Spending Limit Card (col-span-3) */}
        <div className="lg:col-span-3 min-w-0">
          <InvestorUtilizationCard
            totalUsed={totalInvestorUsed}
            totalPrincipal={totalInvestorPrincipal}
          />
        </div>

        {/* Bottom Right: Recent Activities Table (col-span-9) */}
        <div className="lg:col-span-9 min-w-0">
          <RecentActivityTable
            activities={activities}
            onSelectActivity={onSelectActivity}
          />
        </div>
      </div>
    </div>
  );
};

export default DashboardOverviewView;
