import React, { useMemo, useState } from 'react';
import { useQueries, useQuery } from '@tanstack/react-query';
import { useAuth } from '../../auth/AuthContext';
import { useAccountingBranches, useAccountingEvents } from '../../api/accountingQueries';
import { garageApi, GarageJob } from '../../api/garageApi';
import { hasCompanyBranchReadRole, useCompanyModuleStates } from '../../api/queries';
import { PageKpiRow } from './PageKpiRow';

const MONEY_PATTERN = /^(-?)(\d+)\.(\d{2})$/;

function parsePaise(value: string | null | undefined): bigint {
  if (!value) return 0n;
  const match = MONEY_PATTERN.exec(value);
  if (!match) return 0n;
  const magnitude = BigInt(match[2]) * 100n + BigInt(match[3]);
  return match[1] === '-' ? -magnitude : magnitude;
}

function formatPaise(paise: bigint): string {
  const negative = paise < 0n;
  const abs = negative ? -paise : paise;
  const whole = abs / 100n;
  const cents = abs % 100n;
  const grouped = new Intl.NumberFormat('en-IN').format(whole);
  return `${negative ? '−' : ''}₹${grouped}.${String(cents).padStart(2, '0')}`;
}

function formatDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
        timeZone: 'Asia/Kolkata',
      });
}

function receiptStatusLabel(row: {
  effect_sign: 1 | -1;
  reversal_of_id: string | null;
  replaces_event_id: string | null;
}): string {
  if (row.effect_sign === -1 || row.reversal_of_id) return 'Reversal';
  if (row.replaces_event_id) return 'Replacement';
  return 'Recorded';
}

export interface GarageRevenueViewProps {
  onOpenGarageJobs?: () => void;
}

export const GarageRevenueView: React.FC<GarageRevenueViewProps> = ({ onOpenGarageJobs }) => {
  const { status, user, currentCompany } = useAuth();
  const companyId = currentCompany?.id ?? '';
  const userId = user?.id ?? '';
  const canRead = status === 'authenticated' && Boolean(companyId) && hasCompanyBranchReadRole(user);
  const isCompanyWideReader = Boolean(
    currentCompany?.company_wide_roles?.some((role) => role === 'accountant' || role === 'owner'),
  );

  const [selectedBranch, setSelectedBranch] = useState<string>('all');
  const [receiptPage, setReceiptPage] = useState(1);
  const [jobsPage, setJobsPage] = useState(1);

  const moduleStatesQuery = useCompanyModuleStates();
  const branchesQuery = useAccountingBranches();

  const branchId = selectedBranch === 'all' ? undefined : selectedBranch;
  const eventsQuery = useAccountingEvents({
    page: receiptPage,
    eventType: 'GARAGE_RECEIPT',
    branchId,
    enabled: canRead,
  });

  const jobsQuery = useQuery({
    queryKey: userId && companyId
      ? ['garage', userId, companyId, 'jobs', 'revenue', jobsPage]
      : ['garage', 'unavailable', 'jobs', 'revenue', jobsPage],
    queryFn: ({ signal }) => garageApi.jobs(companyId, jobsPage, signal),
    enabled: canRead,
    retry: false,
  });

  const branches = branchesQuery.data ?? [];
  const receiptEvents = useMemo(() => eventsQuery.data?.results ?? [], [eventsQuery.data]);

  const externalJobsList: GarageJob[] = useMemo(() => {
    const rows = jobsQuery.data?.results ?? [];
    return rows.filter(
      (job) => job.context === 'EXTERNAL_CUSTOMER' && (!branchId || job.branch_id === branchId),
    );
  }, [jobsQuery.data, branchId]);

  const detailQueries = useQueries({
    queries: externalJobsList.map((job) => ({
      queryKey: ['garage', userId, companyId, 'job', job.id] as const,
      queryFn: ({ signal }: { signal: AbortSignal }) => garageApi.job(companyId, job.id, signal),
      enabled: canRead && job.customer_charge === undefined,
      retry: false,
    })),
  });

  const externalJobs: GarageJob[] = useMemo(
    () => externalJobsList.map((job, idx) => detailQueries[idx]?.data ?? job),
    [externalJobsList, detailQueries],
  );

  const detailsPending = detailQueries.some((q) => q.isPending);
  const detailsError = detailQueries.some((q) => q.isError);

  const actualReceiptsPaise = useMemo(
    () =>
      receiptEvents.reduce(
        (sum, row) => sum + parsePaise(row.amount) * BigInt(row.effect_sign),
        0n,
      ),
    [receiptEvents],
  );

  const billedChargesPaise = useMemo(
    () => externalJobs.reduce((sum, job) => sum + parsePaise(job.customer_charge), 0n),
    [externalJobs],
  );

  const outstandingPaise = useMemo(
    () => externalJobs.reduce((sum, job) => sum + parsePaise(job.outstanding), 0n),
    [externalJobs],
  );

  const garageModuleState = moduleStatesQuery.data?.modules.find((m) => m.code === 'garage')?.state;
  const accountingModuleState = moduleStatesQuery.data?.modules.find((m) => m.code === 'accounting')?.state;
  const kpiStatus: 'loading' | 'unavailable' | 'ready' = !canRead || eventsQuery.isError || jobsQuery.isError || detailsError
    ? 'unavailable'
    : eventsQuery.isPending || jobsQuery.isPending || detailsPending
      ? 'loading'
      : 'ready';

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-[var(--theme-primary)]">
            Company Accounting · Garage source
          </div>
          <h1 className="mt-0.5 text-xl font-extrabold text-gray-950 dark:text-white">
            Garage Revenue
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Actual Accounting GARAGE_RECEIPT events vs billed Customer Job charges and outstanding receivables.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor="garage-revenue-branch-filter">
            Filter by Branch
          </label>
          <select
            id="garage-revenue-branch-filter"
            aria-label="Filter by Branch"
            value={selectedBranch}
            onChange={(event) => {
              setSelectedBranch(event.target.value);
              setReceiptPage(1);
            }}
            className="rounded-xl border border-[#e2d8ce] bg-white px-3 py-2 text-xs font-semibold text-gray-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          >
            {isCompanyWideReader && <option value="all">All Branches</option>}
            {!isCompanyWideReader && <option value="all">Authorized Branches</option>}
            {branches.map((branch) => (
              <option key={branch.id} value={branch.id}>
                {branch.name}
              </option>
            ))}
          </select>

          {onOpenGarageJobs && (
            <button
              type="button"
              onClick={onOpenGarageJobs}
              className="rounded-full bg-[#18181b] px-4 py-2 text-xs font-bold text-white hover:opacity-90 dark:bg-white dark:text-black"
            >
              Open Garage Jobs
            </button>
          )}
        </div>
      </header>

      {(garageModuleState === 'disabled' || accountingModuleState === 'disabled') && (
        <div
          role="status"
          className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200"
        >
          {garageModuleState === 'disabled' ? 'Garage' : 'Accounting'} module is currently OFF. Historical records remain readable while new postings are blocked.
        </div>
      )}

      <PageKpiRow
        status={kpiStatus}
        items={[
          { label: 'Actual Garage Receipts (Page)', value: formatPaise(actualReceiptsPaise) },
          { label: 'Customer Job Charges (Page)', value: formatPaise(billedChargesPaise) },
          { label: 'Outstanding Receivable (Page)', value: formatPaise(outstandingPaise) },
          { label: 'Garage Receipt Events', value: String(eventsQuery.data?.count ?? 0) },
        ]}
      />

      {!canRead ? (
        <p role="alert" className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-gray-300">
          An authorized Company or Branch account is required to view Garage Revenue.
        </p>
      ) : (
        <>
          <section
            aria-label="Actual Garage Receipts"
            className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-sm font-bold text-gray-950 dark:text-white">
                  Actual Garage Receipts (Accounting Events)
                </h2>
                <p className="text-[11px] text-gray-500 dark:text-gray-400">
                  Authoritative GARAGE_RECEIPT cash/bank inflow events, including reversals and corrections.
                </p>
              </div>
              <span className="text-xs text-gray-500">
                {eventsQuery.isSuccess ? `${eventsQuery.data.count} total events` : ''}
              </span>
            </div>

            {eventsQuery.isPending && <p role="status" className="py-4 text-xs text-gray-500">Loading receipt events…</p>}
            {eventsQuery.isError && (
              <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
                Actual Garage receipt events are unavailable right now.
              </p>
            )}
            {eventsQuery.isSuccess && receiptEvents.length === 0 && (
              <p className="py-4 text-xs text-gray-500">No Garage receipt events recorded for this selection.</p>
            )}
            {eventsQuery.isSuccess && receiptEvents.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 text-[11px] font-bold uppercase tracking-wide text-gray-500 dark:border-zinc-800">
                      <th className="py-2 pr-3">Effective Date</th>
                      <th className="py-2 pr-3">Branch</th>
                      <th className="py-2 pr-3">Reference</th>
                      <th className="py-2 pr-3">Status</th>
                      <th className="py-2 pr-3 text-right">Signed Amount</th>
                      <th className="py-2">Event ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {receiptEvents.map((row) => (
                      <tr key={row.id} className="border-b border-gray-100 last:border-0 dark:border-zinc-800/70">
                        <td className="py-2.5 pr-3 whitespace-nowrap text-gray-700 dark:text-gray-300">
                          {formatDate(row.effective_at)}
                        </td>
                        <td className="py-2.5 pr-3 text-gray-700 dark:text-gray-300">
                          {row.branch_name ?? 'Company-wide'}
                        </td>
                        <td className="py-2.5 pr-3 font-semibold text-gray-900 dark:text-white">
                          {row.source_reference || row.description || '—'}
                        </td>
                        <td className="py-2.5 pr-3">
                          <span
                            className={
                              row.effect_sign === -1
                                ? 'rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700 dark:bg-red-950/50 dark:text-red-300'
                                : 'rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                            }
                          >
                            {receiptStatusLabel(row)}
                          </span>
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold text-gray-950 dark:text-white">
                          {formatPaise(parsePaise(row.amount) * BigInt(row.effect_sign))}
                        </td>
                        <td className="py-2.5 font-mono text-[11px] text-gray-500" title={row.id}>
                          {row.id.slice(0, 8)}…
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {eventsQuery.isSuccess && (eventsQuery.data.previous || eventsQuery.data.next) && (
              <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-3 text-xs dark:border-zinc-800">
                <span>Page {receiptPage}</span>
                <div className="flex gap-3">
                  <button
                    type="button"
                    disabled={!eventsQuery.data.previous || receiptPage <= 1}
                    onClick={() => setReceiptPage((p) => Math.max(1, p - 1))}
                    className="font-bold disabled:opacity-40"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={!eventsQuery.data.next}
                    onClick={() => setReceiptPage((p) => p + 1)}
                    className="font-bold disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </section>

          <section
            aria-label="Customer Job Charges & Outstanding"
            className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-sm font-bold text-gray-950 dark:text-white">
                  Customer Job Charges &amp; Outstanding
                </h2>
                <p className="text-[11px] text-gray-500 dark:text-gray-400">
                  Billed charges create receivables; only recorded GARAGE_RECEIPT events count as cash received.
                </p>
              </div>
              <span className="text-xs text-gray-500">
                {jobsQuery.isSuccess ? `${externalJobs.length} external customer jobs on page ${jobsPage}` : ''}
              </span>
            </div>

            {jobsQuery.isPending && <p role="status" className="py-4 text-xs text-gray-500">Loading customer jobs…</p>}
            {jobsQuery.isError && (
              <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
                Customer job charges are unavailable right now.
              </p>
            )}
            {jobsQuery.isSuccess && externalJobs.length === 0 && (
              <p className="py-4 text-xs text-gray-500">No external customer jobs found on this page.</p>
            )}
            {jobsQuery.isSuccess && externalJobs.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[680px] border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 text-[11px] font-bold uppercase tracking-wide text-gray-500 dark:border-zinc-800">
                      <th className="py-2 pr-3">Vehicle</th>
                      <th className="py-2 pr-3">Branch</th>
                      <th className="py-2 pr-3">Customer</th>
                      <th className="py-2 pr-3">Status</th>
                      <th className="py-2 pr-3 text-right">Charge (Billed)</th>
                      <th className="py-2 pr-3 text-right">Received</th>
                      <th className="py-2 text-right">Outstanding</th>
                    </tr>
                  </thead>
                  <tbody>
                    {externalJobs.map((job) => (
                      <tr key={job.id} className="border-b border-gray-100 last:border-0 dark:border-zinc-800/70">
                        <td className="py-2.5 pr-3">
                          <div className="font-semibold text-gray-950 dark:text-white">{job.vehicle_registration}</div>
                          <div className="text-[11px] text-gray-500">{job.vehicle_model}</div>
                        </td>
                        <td className="py-2.5 pr-3 text-gray-700 dark:text-gray-300">{job.branch_name}</td>
                        <td className="py-2.5 pr-3 text-gray-700 dark:text-gray-300">
                          {job.contact_name || '—'}
                          {job.contact_phone ? ` · ${job.contact_phone}` : ''}
                        </td>
                        <td className="py-2.5 pr-3 font-semibold text-gray-700 dark:text-gray-300">
                          {job.status === 'OPEN' ? 'Open' : 'Completed'}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-semibold text-gray-900 dark:text-white">
                          {job.customer_charge != null ? formatPaise(parsePaise(job.customer_charge)) : '—'}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-semibold text-emerald-700 dark:text-emerald-300">
                          {formatPaise(parsePaise(job.received))}
                        </td>
                        <td className="py-2.5 text-right font-mono font-bold text-gray-950 dark:text-white">
                          {job.outstanding != null ? formatPaise(parsePaise(job.outstanding)) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {jobsQuery.isSuccess && (jobsQuery.data.previous || jobsQuery.data.next) && (
              <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-3 text-xs dark:border-zinc-800">
                <span>Jobs page {jobsPage}</span>
                <div className="flex gap-3">
                  <button
                    type="button"
                    disabled={!jobsQuery.data.previous || jobsPage <= 1}
                    onClick={() => setJobsPage((p) => Math.max(1, p - 1))}
                    className="font-bold disabled:opacity-40"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={!jobsQuery.data.next}
                    onClick={() => setJobsPage((p) => p + 1)}
                    className="font-bold disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
};

export default GarageRevenueView;
