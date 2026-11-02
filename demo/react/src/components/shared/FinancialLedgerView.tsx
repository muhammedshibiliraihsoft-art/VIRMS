import React, { useState } from 'react';
import {
  DollarSign,
  Plus,
  Search,
  Filter,
  ArrowUpRight,
  ArrowDownLeft,
  Calendar,
  Building2,
  FileText,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { Data, Garage } from '../../types';
import {
  companyReportValues,
  fundPosition,
  capitalReport,
  salePrice,
  buyerNetReceived,
  buyerReceivable,
  effectiveExpense,
  paid,
} from '../../utils/selectors';
import { FormModalType } from './SharedFormModal';
import { useCanPresentBusinessWriteActions } from '../../auth/RolePresentationContext';
import { getFormDataSourceStatus } from '../../data/navigationRegistry';
import { DemoBadge } from './DemoBadge';

interface FinancialLedgerViewProps {
  routeKey: string;
  data: Data;
  garages: Garage[];
  selectedGarage: string;
  onSelectGarage: (garageId: string) => void;
  onOpenFormModal: (type: FormModalType, initialContext?: Record<string, any>) => void;
}

export const FinancialLedgerView: React.FC<FinancialLedgerViewProps> = ({
  routeKey,
  data,
  garages,
  selectedGarage,
  onSelectGarage,
  onOpenFormModal,
}) => {
  const canPresentWriteActions = useCanPresentBusinessWriteActions();
  const [searchQuery, setSearchQuery] = useState('');
  const inScope = (gId: string) => selectedGarage === 'all' || gId === selectedGarage;
  const formatINR = (val?: number) =>
    '₹' + Math.round(val || 0).toLocaleString('en-IN');

  // Derive title, primary metric cards, action button, and table rows
  let title = routeKey;
  let subtitle = 'Financial Overview & Source Ledger';
  let primaryButton: { label: string; formType: FormModalType } | null = null;
  let kpis: { label: string; value: string; isOrange?: boolean }[] = [];
  let columns: { key: string; label: string; align?: 'left' | 'right' | 'center' }[] = [];
  let rows: Record<string, any>[] = [];

  switch (routeKey) {
    case 'Investor Fund': {
      title = 'Investor Fund Operations';
      subtitle = 'Investor capital accounts, fund history, and available drawing balances';
      primaryButton = { label: 'Add Capital Credit', formType: 'fundCredit' };

      const totalPrincipal = (data.investors || []).reduce((s, i) => s + i.principal, 0);
      const totalAvailable = (data.investors || []).reduce((s, i) => s + fundPosition(data, i.id).available, 0);
      const totalDeployed = (data.investors || []).reduce((s, i) => s + fundPosition(data, i.id).used, 0);

      kpis = [
        { label: 'Available Capital', value: formatINR(totalAvailable), isOrange: true },
        { label: 'Total Principal', value: formatINR(totalPrincipal) },
        { label: 'Deployed in Stock', value: formatINR(totalDeployed) },
      ];

      columns = [
        { key: 'name', label: 'Investor' },
        { key: 'principal', label: 'Opening Principal', align: 'right' },
        { key: 'used', label: 'Deployed', align: 'right' },
        { key: 'available', label: 'Available Balance', align: 'right' },
        { key: 'actions', label: 'Action', align: 'right' },
      ];

      rows = (data.investors || []).map((inv) => {
        const pos = fundPosition(data, inv.id);
        return {
          id: inv.id,
          name: inv.name,
          principal: formatINR(pos.principal),
          used: formatINR(pos.used),
          available: formatINR(pos.available),
          actionType: 'fundCredit',
        };
      });
      break;
    }

    case 'Vehicle Sales': {
      title = 'Vehicle Sales Register';
      subtitle = 'Binding vehicle sales, contracted prices, and collections progress';
      primaryButton = { label: 'Record New Sale', formType: 'sale' };

      const totalSalesValue = (data.sales || []).reduce((s, x) => s + salePrice(x), 0);
      const totalCollected = (data.sales || []).reduce((s, x) => s + buyerNetReceived(data, x), 0);
      const totalDue = (data.sales || []).reduce((s, x) => s + buyerReceivable(data, x), 0);

      kpis = [
        { label: 'Total Contracted', value: formatINR(totalSalesValue), isOrange: true },
        { label: 'Collected to Date', value: formatINR(totalCollected) },
        { label: 'Outstanding Due', value: formatINR(totalDue) },
      ];

      columns = [
        { key: 'vehicle', label: 'Vehicle' },
        { key: 'buyer', label: 'Buyer Name' },
        { key: 'price', label: 'Sale Price', align: 'right' },
        { key: 'received', label: 'Net Collected', align: 'right' },
        { key: 'due', label: 'Balance Due', align: 'right' },
        { key: 'actions', label: 'Action', align: 'right' },
      ];

      rows = (data.sales || []).map((s) => {
        const veh = (data.vehicles || []).find((v) => v.id === s.vehicleId);
        const finalPrice = salePrice(s);
        const rcvd = buyerNetReceived(data, s);
        const due = buyerReceivable(data, s);
        return {
          id: s.id,
          vehicle: veh ? `${veh.model} · ${veh.number}` : '—',
          buyer: s.buyer,
          price: formatINR(finalPrice),
          received: formatINR(rcvd),
          due: formatINR(due),
          actionType: due > 0 ? 'collection' : 'saleCorrection',
          actionLabel: due > 0 ? 'Record Collection' : 'Correct Price',
        };
      });
      break;
    }

    case 'Collections': {
      title = 'Payment Collections Ledger';
      subtitle = 'Verified payment receipts logged across sales, jobs, and capital';
      primaryButton = { label: 'Record Collection', formType: 'collection' };

      const totalCollections = (data.payments || []).reduce((s, p) => s + p.amount, 0);
      const buyerCollections = (data.payments || [])
        .filter((p) => p.kind === 'buyer')
        .reduce((s, p) => s + p.amount, 0);
      const customerCollections = (data.payments || [])
        .filter((p) => p.kind === 'customer')
        .reduce((s, p) => s + p.amount, 0);

      kpis = [
        { label: 'Total Collections', value: formatINR(totalCollections), isOrange: true },
        { label: 'Buyer Vehicle Receipts', value: formatINR(buyerCollections) },
        { label: 'Customer Job Receipts', value: formatINR(customerCollections) },
      ];

      columns = [
        { key: 'date', label: 'Date' },
        { key: 'kind', label: 'Stream' },
        { key: 'target', label: 'Target / Reference' },
        { key: 'method', label: 'Method' },
        { key: 'amount', label: 'Amount', align: 'right' },
      ];

      rows = (data.payments || []).map((p) => {
        let targetDesc = p.targetId;
        if (p.kind === 'customer') {
          const j = (data.jobs || []).find((x) => x.id === p.targetId);
          if (j) targetDesc = `${j.number} (${j.description})`;
        } else if (p.kind === 'buyer') {
          const s = (data.sales || []).find((x) => x.id === p.targetId);
          if (s) targetDesc = `Sale to ${s.buyer}`;
        }
        return {
          id: p.id,
          date: p.date,
          kind: p.kind.toUpperCase(),
          target: targetDesc,
          method: p.method,
          amount: formatINR(p.amount),
        };
      });
      break;
    }

    case 'Sale Corrections & Refunds': {
      title = 'Sale Corrections & Buyer Refunds';
      subtitle = 'Immutable price corrections and principal-backed buyer refunds';
      primaryButton = { label: 'Process Buyer Refund', formType: 'refund' };

      const totalRefunded = (data.buyerRefunds ?? []).reduce((s, r) => s + r.amount, 0);
      const totalCorrectedSales = (data.sales || []).filter((s) => (s.corrections?.length ?? 0) > 0).length;

      kpis = [
        { label: 'Buyer Refunds Paid', value: formatINR(totalRefunded), isOrange: true },
        { label: 'Sales Corrected', value: String(totalCorrectedSales) },
      ];

      columns = [
        { key: 'date', label: 'Date' },
        { key: 'type', label: 'Adjustment Type' },
        { key: 'target', label: 'Sale / Buyer' },
        { key: 'reason', label: 'Reason' },
        { key: 'amount', label: 'Amount / New Price', align: 'right' },
      ];

      const refundRows = (data.buyerRefunds ?? []).map((r) => {
        const s = (data.sales || []).find((x) => x.id === r.saleId);
        return {
          id: r.id,
          date: r.date,
          type: 'Buyer Refund',
          target: s ? `Sale: ${s.buyer}` : r.saleId,
          reason: r.reason,
          amount: formatINR(r.amount),
        };
      });

      const correctionRows: any[] = [];
      (data.sales || []).forEach((s) => {
        (s.corrections ?? []).forEach((c) => {
          correctionRows.push({
            id: c.id,
            date: c.date,
            type: 'Sale Correction',
            target: `Sale: ${s.buyer}`,
            reason: c.reason,
            amount: formatINR(c.price),
          });
        });
      });

      rows = [...refundRows, ...correctionRows];
      break;
    }

    case 'Garage Revenue': {
      title = 'Garage Revenue Ledger';
      subtitle = 'Work order billable charges, receipts and customer receivables';
      primaryButton = { label: 'Record Customer Receipt', formType: 'customerReceipt' };

      const comp = companyReportValues(data, selectedGarage);
      const totalCharge = (data.jobs || [])
        .filter((j) => inScope(j.garageId))
        .reduce((s, j) => s + j.charge, 0);
      const totalDue = Math.max(0, totalCharge - comp.customerReceipts);

      kpis = [
        { label: 'Customer Receipts', value: formatINR(comp.customerReceipts), isOrange: true },
        { label: 'Total Invoiced', value: formatINR(totalCharge) },
        { label: 'Outstanding Balance', value: formatINR(totalDue) },
      ];

      columns = [
        { key: 'job', label: 'Work Order' },
        { key: 'garage', label: 'Branch' },
        { key: 'charge', label: 'Total Invoiced', align: 'right' },
        { key: 'received', label: 'Received', align: 'right' },
        { key: 'due', label: 'Balance Due', align: 'right' },
        { key: 'actions', label: 'Action', align: 'right' },
      ];

      rows = (data.jobs || [])
        .filter((j) => inScope(j.garageId))
        .map((j) => {
          const garageName = (data.garages || []).find((g) => g.id === j.garageId)?.name ?? 'Central';
          const rcvd = j.received + paid(data, 'customer', j.id);
          const due = Math.max(0, j.charge - rcvd);
          return {
            id: j.id,
            job: `${j.number} · ${j.description}`,
            garage: garageName,
            charge: formatINR(j.charge),
            received: formatINR(rcvd),
            due: formatINR(due),
            actionType: 'customerReceipt',
            actionLabel: 'Record Receipt',
          };
        });
      break;
    }

    case 'Company Income': {
      title = 'Company Other Income';
      subtitle = 'Direct non-job operational revenue (scrap metal, recycling, recoveries)';
      primaryButton = { label: 'Record Other Income', formType: 'otherIncome' };

      const totalOtherIncome = (data.otherIncomeReceipts ?? [])
        .filter((r) => inScope(r.garageId))
        .reduce((s, r) => s + r.amount, 0);

      kpis = [
        { label: 'Total Other Income', value: formatINR(totalOtherIncome), isOrange: true },
      ];

      columns = [
        { key: 'date', label: 'Timestamp' },
        { key: 'source', label: 'Source' },
        { key: 'description', label: 'Description' },
        { key: 'method', label: 'Method' },
        { key: 'amount', label: 'Amount', align: 'right' },
      ];

      rows = (data.otherIncomeReceipts ?? [])
        .filter((r) => inScope(r.garageId))
        .map((r) => ({
          id: r.id,
          date: r.timestamp,
          source: r.source,
          description: r.description,
          method: r.method,
          amount: formatINR(r.amount),
        }));
      break;
    }

    case 'Company Expenses': {
      title = 'Company Operating Expenses';
      subtitle = 'Workshop utilities, rent, supplies and overheads';
      primaryButton = { label: 'Add Company Expense', formType: 'companyExpense' };

      const compExpenses = (data.expenses || [])
        .filter((e) => e.category === 'Company' && inScope(e.garageId))
        .reduce((s, e) => s + effectiveExpense(e).amount, 0);

      kpis = [
        { label: 'Total Overhead Expenses', value: formatINR(compExpenses), isOrange: true },
      ];

      columns = [
        { key: 'date', label: 'Date' },
        { key: 'description', label: 'Description' },
        { key: 'garage', label: 'Branch' },
        { key: 'amount', label: 'Amount', align: 'right' },
      ];

      rows = (data.expenses || [])
        .filter((e) => e.category === 'Company' && inScope(e.garageId))
        .map((e) => {
          const g = (data.garages || []).find((x) => x.id === e.garageId);
          return {
            id: e.id,
            date: e.date,
            description: e.description,
            garage: g?.name ?? 'Central',
            amount: formatINR(effectiveExpense(e).amount),
          };
        });
      break;
    }

    case 'Running Capital': {
      title = 'Company Running Capital';
      subtitle = 'Vehicle-linked company capital contribution and recovery tracking';
      primaryButton = { label: 'Record Capital Recovery', formType: 'capitalRecovery' };

      const cap = capitalReport(
        data,
        (data.garages || []).map((g) => g.id)
      );

      kpis = [
        { label: 'Net Open Capital', value: formatINR(cap.companyOpen), isOrange: true },
        { label: 'Total Company Deployed', value: formatINR(cap.companyContribution) },
        { label: 'Total Recovered', value: formatINR(cap.companyRecovery) },
      ];

      columns = [
        { key: 'vehicle', label: 'Vehicle Number' },
        { key: 'contribution', label: 'Company Investment', align: 'right' },
        { key: 'recovery', label: 'Recovered', align: 'right' },
        { key: 'open', label: 'Open Balance', align: 'right' },
        { key: 'actions', label: 'Action', align: 'right' },
      ];

      rows = cap.rows.map((r) => ({
        id: r.vehicleId,
        vehicle: r.vehicleNumber,
        contribution: formatINR(r.contribution),
        recovery: formatINR(r.recovery),
        open: formatINR(r.open),
        actionType: 'capitalRecovery',
        actionLabel: 'Recover Capital',
      }));
      break;
    }

    case 'Transactions': {
      title = 'Transaction Register';
      subtitle = 'Unified chronological feed of system financial transactions';
      primaryButton = null;

      const totalTransactions =
        (data.payments?.length ?? 0) +
        (data.expenses?.length ?? 0) +
        (data.otherIncomeReceipts?.length ?? 0);

      kpis = [
        { label: 'Total Logged Events', value: String(totalTransactions), isOrange: true },
      ];

      columns = [
        { key: 'date', label: 'Date' },
        { key: 'type', label: 'Event Type' },
        { key: 'description', label: 'Description' },
        { key: 'amount', label: 'Amount', align: 'right' },
      ];

      const pRows = (data.payments || []).map((p) => ({
        id: p.id,
        date: p.date,
        type: `Payment (${p.kind})`,
        description: `Target ${p.targetId} via ${p.method}`,
        amount: formatINR(p.amount),
      }));

      const eRows = (data.expenses || []).map((e) => ({
        id: e.id,
        date: e.date,
        type: `Expense (${e.category})`,
        description: e.description,
        amount: '-' + formatINR(effectiveExpense(e).amount),
      }));

      const iRows = (data.otherIncomeReceipts || []).map((i) => ({
        id: i.id,
        date: i.timestamp.slice(0, 10),
        type: 'Other Income',
        description: `${i.source} · ${i.description}`,
        amount: formatINR(i.amount),
      }));

      rows = [...pRows, ...eRows, ...iRows].sort((a, b) => b.date.localeCompare(a.date));
      break;
    }

    case 'Audit & Corrections': {
      title = 'Audit Log & Change Register';
      subtitle = 'Immutable record of modifications, price adjustments and transactions';
      primaryButton = null;

      kpis = [
        { label: 'Logged Actions', value: String(data.audit.length), isOrange: true },
      ];

      columns = [
        { key: 'date', label: 'Timestamp' },
        { key: 'action', label: 'Action' },
        { key: 'detail', label: 'Event Detail' },
      ];

      rows = data.audit.map((a) => ({
        id: a.id,
        date: a.date,
        action: a.action,
        detail: a.detail,
      }));
      break;
    }

    default:
      break;
  }

  const filteredRows = rows.filter((r) => {
    if (!searchQuery.trim()) return true;
    return Object.values(r).some((val) =>
      String(val).toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="space-y-4 sm:space-y-5 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-[#f2ebe5] dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">
            VIRMS ACCOUNTING WORKSPACE
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            {title}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium">
            {subtitle}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Garage Filter */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-zinc-800 border border-[#e2d8ce] dark:border-zinc-700 text-xs font-semibold text-gray-700 dark:text-gray-300">
            <Building2 className="w-3.5 h-3.5 text-gray-500" />
            <select
              value={selectedGarage}
              onChange={(e) => onSelectGarage(e.target.value)}
              className="bg-transparent border-none focus:outline-none cursor-pointer pr-2 font-bold"
            >
              <option value="all">All Garages</option>
              {garages.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>

          {/* Primary Action Button */}
          {canPresentWriteActions && primaryButton && (
            <button
              onClick={() => onOpenFormModal(primaryButton!.formType)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#18181b] hover:bg-black text-white text-xs font-bold shadow-xs transition cursor-pointer active:scale-95"
            >
              <Plus className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
              <span className="min-w-0 truncate">{primaryButton.label}</span>
              {getFormDataSourceStatus(primaryButton.formType) === 'demo' && <DemoBadge size="compact" />}
            </button>
          )}
        </div>
      </div>

      {/* Primary KPI Cards */}
      {kpis.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {kpis.map((kpi, idx) => (
            <div
              key={idx}
              className={`rounded-[24px] p-4 flex flex-col justify-between min-h-[84px] max-h-[96px] ${
                kpi.isOrange
                  ? 'dashboard-card-orange text-white shadow-xs'
                  : 'dashboard-card-solid'
              }`}
            >
              <span
                className={`text-[11px] font-medium leading-none ${
                  kpi.isOrange ? 'text-white/90' : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                {kpi.label}
              </span>
              <span
                className={`text-2xl sm:text-[27px] font-bold tracking-tight my-auto ${
                  kpi.isOrange ? 'text-white' : 'text-gray-950 dark:text-white'
                }`}
              >
                {kpi.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Main Ledger Card */}
      <div className="dashboard-card-solid rounded-[24px] overflow-hidden">
        {/* Table Search & Filter Bar */}
        <div className="p-4 px-5 border-b border-[#f0e7df] dark:border-zinc-800 flex items-center justify-between gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder={`Search ${title.toLowerCase()}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-full text-xs bg-gray-50 dark:bg-zinc-800/60 border border-[#e2d8ce] dark:border-zinc-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary)]"
            />
          </div>

          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">
            {filteredRows.length} record{filteredRows.length !== 1 ? 's' : ''} listed
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#f0e7df] dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/30">
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={`py-3 px-4 text-[11px] font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider ${
                      col.align === 'right'
                        ? 'text-right'
                        : col.align === 'center'
                        ? 'text-center'
                        : 'text-left'
                    }`}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f5ede5] dark:divide-zinc-800/60">
              {filteredRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="py-12 text-center text-xs text-gray-500 dark:text-gray-400 font-medium"
                  >
                    No records found in this view.
                  </td>
                </tr>
              ) : (
                filteredRows.map((r, idx) => (
                  <tr
                    key={r.id || idx}
                    className="hover:bg-gray-50/70 dark:hover:bg-zinc-800/40 transition-colors"
                  >
                    {columns.map((col) => {
                      if (col.key === 'actions') {
                        return (
                          <td key={col.key} className="py-3 px-4 text-right">
                            {canPresentWriteActions && r.actionType && (
                              <button
                                onClick={() =>
                                  onOpenFormModal(r.actionType, {
                                    saleId: r.id,
                                    jobId: r.id,
                                    vehicleId: r.id,
                                    investorId: r.id,
                                  })
                                }
                                className="inline-flex items-center gap-1 text-[11px] font-bold text-[var(--theme-primary)] hover:text-[var(--theme-primary-hover)] px-2 py-0.5 rounded-md hover:bg-[var(--theme-primary-soft)] transition cursor-pointer"
                              >
                                <span>{r.actionLabel || 'Action'}</span>
                                {getFormDataSourceStatus(r.actionType) === 'demo' && <DemoBadge size="compact" />}
                              </button>
                            )}
                          </td>
                        );
                      }
                      return (
                        <td
                          key={col.key}
                          className={`py-3 px-4 font-medium text-gray-900 dark:text-gray-100 ${
                            col.align === 'right'
                              ? 'text-right font-mono font-semibold'
                              : col.align === 'center'
                              ? 'text-center'
                              : 'text-left'
                          }`}
                        >
                          {r[col.key]}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
