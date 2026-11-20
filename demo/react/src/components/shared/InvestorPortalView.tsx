import React, { useState } from 'react';
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, ArrowDownLeft, CarFront, Clock3, RefreshCw, ShieldCheck } from 'lucide-react';
import { phase5Api } from '../../api/phase5Api';
import { queryKeys } from '../../api/queryKeys';
import { useAuth } from '../../auth/AuthContext';

type Props = { routeKey: string };

const routeTitles: Record<string, string> = {
  Dashboard: 'My Investor Overview',
  'Investor Fund': 'My Fund Position',
  'Stock / Investor': 'My Stock Vehicles',
  'Investor Profit & Interim': 'Profit & Interim',
  'Reconciliation & Settlement': 'Reconciliation & Exit',
};

function money(value: string | null | undefined) {
  if (!value) return '—';
  if (!/^-?\d+\.\d{2}$/.test(value)) return '—';
  const negative = value.startsWith('-');
  const unsigned = negative ? value.slice(1) : value;
  const [whole, fraction] = unsigned.split('.');
  const grouped = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(BigInt(whole));
  return `${negative ? '-' : ''}₹${grouped}.${fraction}`;
}

function date(value: string | null | undefined) {
  if (!value) return '—';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? '—' : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(parsed);
}

export const InvestorPortalView: React.FC<Props> = ({ routeKey }) => {
  const { status, user, currentCompany } = useAuth();
  const queryClient = useQueryClient();
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [cancellationReason, setCancellationReason] = useState('');
  const queryKey = currentCompany && user ? queryKeys.phase5.investorPortal(user.id, currentCompany.id) : ['investor-portal', 'unavailable'];
  const profileQuery = useQuery({
    queryKey,
    queryFn: ({ signal }) => currentCompany ? phase5Api.investorPortalSelf(currentCompany.id, signal) : Promise.reject(new Error('A verified Company is required.')),
    enabled: status === 'authenticated' && Boolean(user && currentCompany),
    retry: false,
  });
  const showFund = routeKey === 'Investor Fund' || routeKey === 'Dashboard';
  const fundHistoryQuery = useInfiniteQuery({
    queryKey: currentCompany && user
      ? queryKeys.phase5.investorFundHistory(user.id, currentCompany.id)
      : ['investor-fund-history', 'unavailable'],
    queryFn: ({ pageParam, signal }) => currentCompany
      ? phase5Api.investorPortalFundHistory(currentCompany.id, pageParam, signal)
      : Promise.reject(new Error('A verified Company is required.')),
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) => lastPage.next ? pages.length + 1 : undefined,
    enabled: status === 'authenticated' && Boolean(user && currentCompany && profileQuery.data) && showFund,
    retry: false,
  });
  const showProfit = routeKey === 'Investor Profit & Interim' || routeKey === 'Dashboard';
  const interimHistoryQuery = useInfiniteQuery({
    queryKey: currentCompany && user
      ? queryKeys.phase5.investorInterimPaymentHistory(user.id, currentCompany.id)
      : ['investor-interim-history', 'unavailable'],
    queryFn: ({ pageParam, signal }) => currentCompany
      ? phase5Api.investorPortalInterimPaymentHistory(currentCompany.id, pageParam, signal)
      : Promise.reject(new Error('A verified Company is required.')),
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) => lastPage.next ? pages.length + 1 : undefined,
    enabled: status === 'authenticated' && Boolean(user && currentCompany && profileQuery.data) && showProfit,
    retry: false,
  });
  const fundHistory = fundHistoryQuery.data?.pages.flatMap((page) => page.results) ?? [];
  const interimHistory = interimHistoryQuery.data?.pages.flatMap((page) => page.results) ?? [];
  const refresh = async () => {
    await profileQuery.refetch();
    if (showFund) await fundHistoryQuery.refetch();
    if (showProfit) await interimHistoryQuery.refetch();
  };
  const refreshAfterMutation = async () => {
    await queryClient.invalidateQueries({ queryKey });
    await profileQuery.refetch();
    setTermsAccepted(false);
    setCancellationReason('');
  };
  const exitMutation = useMutation({
    mutationFn: () => currentCompany && user ? phase5Api.requestInvestorExit(currentCompany.id, user.id) : Promise.reject(new Error('A verified Investor session is required.')),
    onSuccess: refreshAfterMutation,
  });
  const activeRequest = profileQuery.data?.exit_requests.find((request) => request.status === 'REQUESTED' || request.status === 'CANCELLATION_PENDING');
  const cancellationMutation = useMutation({
    mutationFn: () => currentCompany && user && activeRequest
      ? phase5Api.requestInvestorExitCancellation(currentCompany.id, user.id, activeRequest.id, cancellationReason.trim())
      : Promise.reject(new Error('An active Exit request is required.')),
    onSuccess: refreshAfterMutation,
  });

  const pageTitle = routeTitles[routeKey] ?? routeTitles.Dashboard;
  if (profileQuery.isLoading) return <div className="rounded-2xl border border-gray-200 bg-white p-5 text-sm text-gray-500 dark:border-zinc-800 dark:bg-zinc-900" role="status">Loading your private Investor information…</div>;
  if (profileQuery.isError || !profileQuery.data) return (
    <section className="mx-auto max-w-3xl rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100" role="alert">
      <div className="flex items-start gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><div className="min-w-0"><h1 className="font-bold">Investor information is unavailable</h1><p className="mt-1 text-xs">The server could not verify an active Investor account for this Company. Private financial details remain hidden.</p><button type="button" onClick={() => void refresh()} className="mt-3 inline-flex h-9 items-center gap-1.5 rounded-lg border border-amber-300 px-3 text-xs font-bold dark:border-amber-800"><RefreshCw className="h-3.5 w-3.5" />Try again</button></div></div>
    </section>
  );

  const profile = profileQuery.data;
  const fund = profile.fund_position;
  const showVehicles = routeKey === 'Stock / Investor' || routeKey === 'Dashboard';
  const showExit = routeKey === 'Reconciliation & Settlement' || routeKey === 'Dashboard';

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-3.5 pb-8" aria-label="Investor portal">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 pb-3 dark:border-zinc-800">
        <div><p className="text-[10px] font-bold uppercase tracking-widest text-[var(--theme-primary)]">Investor Portal · Private</p><h1 className="mt-1 text-xl font-extrabold text-gray-950 dark:text-white sm:text-2xl">{pageTitle}</h1><p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{profile.name} · Only information linked to your verified account is shown.</p></div>
        <button type="button" onClick={() => void refresh()} disabled={profileQuery.isFetching} className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 text-xs font-bold disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900"><RefreshCw className={`h-3.5 w-3.5 ${profileQuery.isFetching ? 'animate-spin' : ''}`} />Refresh</button>
      </header>

      {(showFund || showProfit) && <section className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4" aria-label="Fund summary">
        <Metric label="Fund credited" value={money(fund.credit_total)} />
        <Metric label="Principal returned" value={money(fund.principal_return_total)} />
        <Metric label="Committed to vehicles" value={money(fund.committed_vehicle_total)} />
        <Metric label="Ledger available" value={money(fund.ledger_available_amount)} />
      </section>}

      {showFund && <section className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
        <div className="flex items-start gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><p><strong>{fund.status === 'MANUAL_REVIEW_REQUIRED' ? 'Manual review required.' : 'Balance shown for information.'}</strong> This ledger amount is not a confirmed withdrawal amount. Principal withdrawal eligibility will appear after the approved Phase 8 reconciliation is available.</p></div>
      </section>}

      {showFund && <section className="rounded-2xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <SectionTitle icon={<ArrowDownLeft className="h-4 w-4" />} title="Fund activity history" count={fundHistoryQuery.data?.pages[0]?.count ?? 0} />
        {fundHistoryQuery.isLoading ? <p className="py-3 text-xs text-gray-500" role="status">Loading your Fund history…</p> : null}
        {fundHistoryQuery.isError && <div className="mt-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200" role="alert"><span>Fund history could not be loaded. Retry after checking your connection.</span><button type="button" onClick={() => void fundHistoryQuery.refetch()} className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-lg border border-red-300 px-3 font-bold dark:border-red-800"><RefreshCw className="h-3.5 w-3.5" />Retry</button></div>}
        {!fundHistoryQuery.isLoading && !fundHistoryQuery.isError && fundHistory.length === 0 && <Empty>No Fund credits, returns, or Vehicle commitments are recorded.</Empty>}
        {fundHistory.length > 0 && <ul className="mt-2 divide-y divide-gray-100 dark:divide-zinc-800">{fundHistory.map((entry) => <li key={`${entry.activity_type}:${entry.id}`} className="grid gap-1 py-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
          <div className="min-w-0"><p className="text-xs font-bold">{activityLabel(entry.activity_type)}{entry.vehicle_registration ? ` · ${entry.vehicle_registration}` : ''}</p><p className="mt-0.5 text-[10px] text-gray-500">{date(entry.effective_at)} · Branch: {entry.branch_name}</p></div>
          <strong className="text-xs tabular-nums sm:text-right">{money(entry.amount)}</strong>
        </li>)}</ul>}
        {fundHistoryQuery.hasNextPage && <button type="button" onClick={() => void fundHistoryQuery.fetchNextPage()} disabled={fundHistoryQuery.isFetchingNextPage} className="mt-2 inline-flex h-9 items-center gap-1.5 rounded-lg border border-gray-200 px-3 text-xs font-bold disabled:opacity-50 dark:border-zinc-700">
          {fundHistoryQuery.isFetchingNextPage ? 'Loading…' : 'Load more'}
        </button>}
      </section>}

      {showVehicles && <section className="rounded-2xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <SectionTitle icon={<CarFront className="h-4 w-4" />} title="My Stock Vehicles" count={profile.vehicles.length} />
        {profile.vehicles.length === 0 ? <Empty>No Investor-funded Vehicles are linked to your profile.</Empty> : <div className="mt-2 divide-y divide-gray-100 dark:divide-zinc-800">{profile.vehicles.map((vehicle) => <article key={vehicle.vehicle_id} className="grid gap-2 py-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
          <div className="min-w-0"><h2 className="truncate text-sm font-bold">{vehicle.registration} · {vehicle.model}</h2><p className="mt-0.5 text-[11px] text-gray-500">Branch: {vehicle.branch_name} · Sale/collection status: {vehicle.sale_status.replaceAll('_', ' ').toLowerCase()}</p></div>
          <div className="text-left sm:text-right"><p className="text-[10px] font-bold uppercase text-gray-400">Result status</p><p className="mt-0.5 text-xs font-bold">{vehicle.confirmed_result_status.replaceAll('_', ' ').toLowerCase()}</p>{vehicle.confirmed_result && <><p className="text-xs">Investor share {money(vehicle.confirmed_result.investor_share_amount)}</p><p className="text-xs text-gray-500">Deal Profit paid {money(vehicle.confirmed_result.deal_profit_paid)}</p></>}</div>
        </article>)}</div>}
      </section>}

      {showProfit && <section className="rounded-2xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <SectionTitle icon={<ArrowDownLeft className="h-4 w-4" />} title="Profit and Interim" count={profile.vehicle_results.length} />
        <div className="mt-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-[11px] text-blue-950 dark:border-blue-900 dark:bg-blue-950/30 dark:text-blue-100">Vehicle results are grouped by Sale date using your Investor-specific calendar{profile.profit_calendar.duration_months ? ` (${profile.profit_calendar.duration_months} months)` : ''}. Gross Profit, Deal Profit paid, Interim paid, Loss, and applied Loss offset are separate recorded/calculation figures. An Accountant-confirmed snapshot records a reviewed calculation only; it does not establish a payable balance, authorize payment, or close settlement.</div>
        <div className="mt-3 rounded-xl border border-gray-100 p-3 dark:border-zinc-800">
          <p className="text-[10px] font-bold uppercase text-gray-400">Profit periods · {profile.profit_period_status.replaceAll('_', ' ').toLowerCase()}</p>
          <p className="mt-1 text-[10px] text-gray-500">{profile.profit_calendar.start_date ? `Starts ${date(profile.profit_calendar.start_date)} · ${profile.profit_calendar.duration_months} months` : 'Calendar starts after the first Fund credit is recorded.'}</p>
          {profile.profit_periods.length ? <ul className="mt-1 divide-y divide-gray-100 dark:divide-zinc-800">{profile.profit_periods.map((period) => <li key={period.period_start} className="grid gap-1 py-2"><div className="flex flex-wrap items-center justify-between gap-1"><span className="text-xs font-semibold">{date(period.period_start)} – {date(period.period_end)} · {period.result_count} Vehicle results</span><span className="text-[10px] font-bold uppercase text-gray-500">{period.reconciliation_status.replaceAll('_', ' ').toLowerCase()}</span></div><span className="text-[11px] tabular-nums">Gross profit {money(period.gross_investor_profit)} · Deal paid {money(period.deal_profit_paid)} · Interim paid {money(period.interim_paid)} · Loss {money(period.investor_loss_share)} · Offset {money(period.loss_offset_applied)}</span>{period.confirmed_snapshot && <div className="rounded-lg bg-gray-50 px-2.5 py-2 text-[11px] dark:bg-zinc-950"><p className="font-semibold">Last Accountant-confirmed calculation: {money(period.confirmed_snapshot.net_position)} · version {period.confirmed_snapshot.version} · {date(period.confirmed_snapshot.confirmed_at)}</p>{period.reconciliation_status === 'RESTATEMENT_REQUIRED' && period.confirmed_snapshot.pending_restatement_adjustment !== null && <p className="mt-1 text-amber-800 dark:text-amber-200">Source records changed. Difference awaiting review: {money(period.confirmed_snapshot.pending_restatement_adjustment)}. This is not a payment or deduction.</p>}<p className="mt-1 text-[10px] text-gray-500">This signed calculation is not a payable or settlement.</p></div>}{!period.confirmed_snapshot && <p className="text-[10px] text-gray-500">Calculation is not yet Accountant-confirmed.</p>}</li>)}</ul> : <Empty>No period calculation is available yet.</Empty>}
          {profile.unassigned_result_count > 0 && <p className="mt-1 text-[11px] font-semibold text-amber-700 dark:text-amber-300">{profile.unassigned_result_count} result(s) need Accountant review and are not included.</p>}
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_2fr]">
          <div className="rounded-xl bg-gray-50 p-3 dark:bg-zinc-950"><p className="text-[10px] font-bold uppercase text-gray-400">Monthly Interim</p><p className="mt-1 text-base font-extrabold">{money(profile.interim.monthly_amount)}</p><p className="mt-1 text-[10px] text-gray-500">{profile.interim.status === 'CONFIGURED' ? `Effective ${date(profile.interim.effective_date)}` : 'No current configuration'}</p><p className="mt-1 text-[10px] text-gray-500">Payout: not reconciled</p></div>
          <div className="rounded-xl border border-gray-100 p-3 dark:border-zinc-800"><p className="text-[10px] font-bold uppercase text-gray-400">Confirmed Vehicle results</p>{profile.vehicle_results.length ? <ul className="mt-1 divide-y divide-gray-100 dark:divide-zinc-800">{profile.vehicle_results.map((result) => <li key={result.vehicle_id} className="flex flex-wrap justify-between gap-1 py-2 text-xs"><span>{date(result.effective_sale_date)} · {result.result_kind.toLowerCase()} · {result.status.toLowerCase().replaceAll('_', ' ')}</span><strong>Investor share {money(result.investor_share_amount)} · offset {money(result.loss_offset_applied)} · paid {money(result.deal_profit_paid)}</strong></li>)}</ul> : <Empty>No confirmed Vehicle result is available.</Empty>}</div>
        </div>
        <div className="mt-3 rounded-xl border border-gray-100 p-3 dark:border-zinc-800">
          <SectionTitle icon={<ArrowDownLeft className="h-4 w-4" />} title="Interim payment history" count={interimHistoryQuery.data?.pages[0]?.count ?? 0} />
          {interimHistoryQuery.isLoading && <p className="py-3 text-xs text-gray-500" role="status">Loading your Interim payment history…</p>}
          {interimHistoryQuery.isError && <div className="mt-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200" role="alert"><span>Interim payment history could not be loaded. Retry after checking your connection.</span><button type="button" onClick={() => void interimHistoryQuery.refetch()} className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-lg border border-red-300 px-3 font-bold dark:border-red-800"><RefreshCw className="h-3.5 w-3.5" />Retry</button></div>}
          {!interimHistoryQuery.isLoading && !interimHistoryQuery.isError && interimHistory.length === 0 && <Empty>No Monthly Interim payments are recorded.</Empty>}
          {interimHistory.length > 0 && <ul className="mt-2 divide-y divide-gray-100 dark:divide-zinc-800">{interimHistory.map((payment) => <li key={payment.id} className="grid gap-1 py-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"><div><p className="text-xs font-bold">Interim payment · {date(payment.period_month)}</p><p className="mt-0.5 text-[10px] text-gray-500">Paid {date(payment.effective_at)}</p></div><strong className="text-xs tabular-nums sm:text-right">{money(payment.amount)}</strong></li>)}</ul>}
          {interimHistoryQuery.hasNextPage && <button type="button" onClick={() => void interimHistoryQuery.fetchNextPage()} disabled={interimHistoryQuery.isFetchingNextPage} className="mt-2 inline-flex h-9 items-center gap-1.5 rounded-lg border border-gray-200 px-3 text-xs font-bold disabled:opacity-50 dark:border-zinc-700">{interimHistoryQuery.isFetchingNextPage ? 'Loading…' : 'Load more'}</button>}
        </div>
      </section>}

      {showExit && <section className="rounded-2xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900 sm:p-4">
        <SectionTitle icon={<Clock3 className="h-4 w-4" />} title="Exit request and settlement" count={profile.exit_requests.length} />
        <p className="mt-2 text-[11px] text-gray-600 dark:text-gray-300">The normal Exit notice is three months. An Accountant may extend the deadline. A notice ending does not automatically settle the account or release committed Fund.</p>
        <p className="mt-1 text-[11px] text-gray-600 dark:text-gray-300">After an Exit request, new Fund credits and new Vehicle purchases using this Fund are blocked. Previously funded work may continue. Cancellation requires Company Accountant approval.</p>
        <p className="mt-1 text-[11px] text-gray-600 dark:text-gray-300">Submitting a request does not withdraw Fund or pay Profit; Company Accountant review and final settlement are separate.</p>
        {profile.exit_requests.length > 0 && <ul className="mt-2 divide-y divide-gray-100 dark:divide-zinc-800">{profile.exit_requests.map((request) => <li key={request.id} className="flex flex-wrap items-center justify-between gap-2 py-2"><div><span className="text-xs font-bold">{request.status.replaceAll('_', ' ')} · requested {date(request.requested_at)}</span>{request.notice_deadline && <p className="mt-1 text-[11px] text-gray-600 dark:text-gray-300">Notice deadline: {date(request.notice_deadline)}{(request.notice_extensions?.length ?? 0) > 0 ? ' · extended by Company Accountant' : ''}</p>}</div><span className="text-[10px] text-gray-500">Terms {request.terms_version} accepted {date(request.terms_accepted_at)}</span></li>)}</ul>}
        {!activeRequest && <div className="mt-3 rounded-xl bg-gray-50 p-3 dark:bg-zinc-950"><label className="flex items-start gap-2 text-xs"><input type="checkbox" checked={termsAccepted} onChange={(event) => setTermsAccepted(event.target.checked)} className="mt-0.5 h-4 w-4 rounded border-gray-300" /><span>I have read and accept the Exit request terms. I understand this is a request only and does not itself settle or pay any amount.</span></label><button type="button" disabled={!termsAccepted || exitMutation.isPending} onClick={() => exitMutation.mutate()} className="mt-2 inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#18181b] px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black"><ShieldCheck className="h-3.5 w-3.5" />{exitMutation.isPending ? 'Submitting…' : 'Submit Exit request'}</button></div>}
        {activeRequest?.status === 'REQUESTED' && <div className="mt-3 flex flex-col gap-2 rounded-xl bg-gray-50 p-3 dark:bg-zinc-950 sm:flex-row sm:items-end"><label className="min-w-0 flex-1 text-[10px] font-bold text-gray-600 dark:text-gray-300">Reason for requesting cancellation <span className="font-normal">(optional)</span><input value={cancellationReason} onChange={(event) => setCancellationReason(event.target.value)} maxLength={500} className="mt-1 h-9 w-full rounded-lg border border-gray-200 bg-white px-2.5 text-xs dark:border-zinc-700 dark:bg-zinc-900" /></label><button type="button" disabled={cancellationMutation.isPending} onClick={() => cancellationMutation.mutate()} className="h-9 shrink-0 rounded-lg border border-gray-300 px-3 text-xs font-bold disabled:opacity-50 dark:border-zinc-700">{cancellationMutation.isPending ? 'Sending…' : 'Request cancellation'}</button></div>}
        {activeRequest?.status === 'CANCELLATION_PENDING' && <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">Cancellation request is pending Company-level Accountant review.</p>}
        {(exitMutation.error || cancellationMutation.error) && <p role="alert" className="mt-2 text-xs text-red-700 dark:text-red-300">{(exitMutation.error || cancellationMutation.error) instanceof Error ? (exitMutation.error || cancellationMutation.error as Error).message : 'The request failed. Refresh before retrying.'}</p>}
      </section>}
    </main>
  );
};

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900"><p className="text-[10px] font-bold uppercase text-gray-400">{label}</p><p className="mt-1 text-base font-extrabold tabular-nums text-gray-950 dark:text-white">{value}</p></div>;
}

function SectionTitle({ icon, title, count }: { icon: React.ReactNode; title: string; count: number }) {
  return <div className="flex items-center justify-between gap-2"><h2 className="flex items-center gap-1.5 text-sm font-extrabold text-gray-950 dark:text-white">{icon}{title}</h2><span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-bold text-gray-600 dark:bg-zinc-800 dark:text-gray-300">{count}</span></div>;
}

function Empty({ children }: React.PropsWithChildren) {
  return <p className="py-3 text-xs text-gray-500">{children}</p>;
}

function activityLabel(type: 'FUND_CREDIT' | 'PRINCIPAL_RETURN' | 'VEHICLE_COMMITMENT' | 'COMMITMENT_ADJUSTMENT') {
  const labels = {
    FUND_CREDIT: 'Fund credited',
    PRINCIPAL_RETURN: 'Principal returned',
    VEHICLE_COMMITMENT: 'Committed to Vehicle',
    COMMITMENT_ADJUSTMENT: 'Vehicle commitment corrected',
  };
  return labels[type];
}
