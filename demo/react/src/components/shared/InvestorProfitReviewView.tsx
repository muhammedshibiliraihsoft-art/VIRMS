import React, { FormEvent, useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../auth/AuthContext';
import { InvestorProfitPosition, phase5Api } from '../../api/phase5Api';
import { InvestorProfitRepaymentForm } from './InvestorProfitRepaymentForm';
import { InvestorProfitFutureAdjustmentForm } from './InvestorProfitFutureAdjustmentForm';
import { InvestorExitPrincipalPaymentForm } from './InvestorExitPrincipalPaymentForm';
import { InvestorExitLossApplicationForm } from './InvestorExitLossApplicationForm';
import { InvestorExitProfitPaymentForm } from './InvestorExitProfitPaymentForm';
import { queryKeys } from '../../api/queryKeys';

function money(value: string) {
  if (!/^-?\d+\.\d{2}$/.test(value)) return '—';
  const negative = value.startsWith('-');
  const unsigned = negative ? value.slice(1) : value;
  const [whole, fraction] = unsigned.split('.');
  const grouped = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(BigInt(whole));
  return `${negative ? '-' : ''}₹${grouped}.${fraction}`;
}

function date(value: string | null) {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return '—';
  const [year, month, day] = value.split('-').map(Number);
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(year, month - 1, day, 12));
}

export const InvestorProfitReviewView: React.FC = () => {
  const { user, currentCompany } = useAuth();
  const queryClient = useQueryClient();
  const canReadConsolidated = Boolean(currentCompany?.company_wide_roles.includes('accountant'));
  const [investorId, setInvestorId] = useState('');
  const [portalLoginId, setPortalLoginId] = useState('');
  const [revokeReason, setRevokeReason] = useState('');
  const [reconciliationReasons, setReconciliationReasons] = useState<Record<string, string>>({});
  const [positionReasons, setPositionReasons] = useState<Record<string, string>>({});
  const [repayment, setRepayment] = useState<{ companyId: string; investorId: string; position: InvestorProfitPosition } | null>(null);
  const [futureAdjustment, setFutureAdjustment] = useState<{ companyId: string; investorId: string; position: InvestorProfitPosition; periodEnd: string } | null>(null);
  const [noticeDeadline, setNoticeDeadline] = useState('');
  const [noticeReason, setNoticeReason] = useState('');
  const [cancellationReviewReason, setCancellationReviewReason] = useState('');
  const [exitCloseReason, setExitCloseReason] = useState('');

  const investorsQuery = useQuery({
    queryKey: currentCompany && user
      ? queryKeys.phase5.investors(user.id, currentCompany.id, 1)
      : ['phase8', 'investors-unavailable'],
    queryFn: async ({ signal }) => {
      if (!currentCompany) throw new Error('A verified Company is required.');
      const rows = [];
      let page = 1;
      let result = await phase5Api.investors(currentCompany.id, page, signal);
      rows.push(...result.results);
      while (result.next) {
        result = await phase5Api.investors(currentCompany.id, ++page, signal);
        rows.push(...result.results);
      }
      return rows;
    },
    enabled: Boolean(user && currentCompany && canReadConsolidated),
    retry: false,
  });

  useEffect(() => {
    const rows = investorsQuery.data ?? [];
    if (!rows.some((row) => row.id === investorId)) setInvestorId(rows[0]?.id ?? '');
  }, [investorId, investorsQuery.data]);

  useEffect(() => {
    setNoticeDeadline('');
    setNoticeReason('');
    setCancellationReviewReason('');
  }, [investorId]);

  const projectionKey = user && currentCompany && investorId
      ? queryKeys.phase5.investorProfitPeriodProjection(user.id, currentCompany.id, investorId)
      : ['phase8', 'investor-profit-periods-unavailable'];
  const projectionQuery = useQuery({
    queryKey: projectionKey,
    queryFn: ({ signal }) => currentCompany && investorId
      ? phase5Api.investorProfitPeriodProjection(currentCompany.id, investorId, signal)
      : Promise.reject(new Error('Select an Investor.')),
    enabled: Boolean(user && currentCompany && canReadConsolidated && investorId),
    retry: false,
  });

  const positionMutation = useMutation({
    mutationFn: (input: { reconciliation_id: string; expected_source_version: string; reason: string }) =>
      currentCompany && user && investorId
        ? phase5Api.confirmInvestorProfitPosition(currentCompany.id, user.id, investorId, input)
        : Promise.reject(new Error('Select an Investor.')),
    onSuccess: async () => {
      setPositionReasons({});
      await queryClient.invalidateQueries({ queryKey: projectionKey });
    },
  });
  const reconciliationMutation = useMutation({
    mutationFn: (input: { period_start: string; expected_source_version: string; reason: string }) =>
      currentCompany && user && investorId
        ? phase5Api.reconcileInvestorProfitPeriod(currentCompany.id, user.id, investorId, input)
        : Promise.reject(new Error('A verified Company, Accountant and Investor are required.')),
    onSuccess: async (reconciliation, input) => {
      queryClient.setQueryData<Awaited<ReturnType<typeof phase5Api.investorProfitPeriodProjection>>>(
        projectionKey,
        (current) => current ? ({
          ...current,
          periods: current.periods.map((period) => period.period_start === input.period_start ? {
            ...period,
            reconciliation_status: 'RECONCILED',
            reconciliation_id: reconciliation.id,
            reconciliation_version: reconciliation.version,
            last_reconciled_net_position: reconciliation.net_position,
            last_restatement_adjustment: reconciliation.restatement_adjustment,
          } : period),
        }) : current,
      );
      setReconciliationReasons((current) => ({
        ...current,
        [investorId + ':' + input.period_start]: '',
      }));
      await queryClient.invalidateQueries({ queryKey: projectionKey });
    },
  });

  const bindingKey = user && currentCompany && investorId
    ? queryKeys.phase5.investorPortalBinding(user.id, currentCompany.id, investorId)
    : ['phase10', 'portal-binding-unavailable'];
  const exitKey = user && currentCompany && investorId
    ? ['companies', user.id, currentCompany.id, 'phase8', 'investor-exit-requests', investorId]
    : ['phase8', 'investor-exit-unavailable'];
  const exitQuery = useQuery({
    queryKey: exitKey,
    queryFn: ({ signal }) => currentCompany && investorId
      ? phase5Api.investorExitRequests(currentCompany.id, investorId, signal)
      : Promise.reject(new Error('Select an Investor.')),
    enabled: Boolean(user && currentCompany && canReadConsolidated && investorId),
    retry: false,
  });
  const activeExit = exitQuery.data?.results.find((entry) => entry.status === 'REQUESTED' || entry.status === 'CANCELLATION_PENDING');
  const settlementQuery = useQuery({
    queryKey: activeExit && user && currentCompany
      ? [...exitKey, activeExit.id, 'settlement-position']
      : ['phase8', 'exit-settlement-unavailable'],
    queryFn: ({ signal }) => currentCompany && investorId && activeExit
      ? phase5Api.investorExitSettlementPosition(currentCompany.id, investorId, activeExit.id, signal)
      : Promise.reject(new Error('An open Exit request is required.')),
    enabled: Boolean(user && currentCompany && canReadConsolidated && investorId && activeExit),
    retry: false,
  });
  const extendNoticeMutation = useMutation({
    mutationFn: () => currentCompany && user && investorId && activeExit && noticeDeadline
      ? phase5Api.extendInvestorExitNotice(currentCompany.id, user.id, investorId, activeExit.id, new Date(noticeDeadline).toISOString(), noticeReason)
      : Promise.reject(new Error('Select an active Exit request and deadline.')),
    onSuccess: async () => {
      setNoticeDeadline('');
      setNoticeReason('');
      await queryClient.invalidateQueries({ queryKey: exitKey });
    },
  });
  const cancellationReviewMutation = useMutation({
    mutationFn: (approve: boolean) => currentCompany && user && investorId && activeExit
      ? phase5Api.reviewInvestorExitCancellation(currentCompany.id, user.id, investorId, activeExit.id, approve, cancellationReviewReason)
      : Promise.reject(new Error('Select a pending Exit cancellation.')),
    onSuccess: async () => {
      setCancellationReviewReason('');
      await queryClient.invalidateQueries({ queryKey: exitKey });
    },
  });
  const exitCloseMutation = useMutation({
    mutationFn: () => currentCompany && user && investorId && activeExit && settlementQuery.data
      ? phase5Api.closeInvestorExitSettlement(currentCompany.id, user.id, investorId, activeExit.id,
          { expected_source_version: settlementQuery.data.source_version, reason: exitCloseReason })
      : Promise.reject(new Error('Reload the current Exit settlement before closing.')),
    onSuccess: async () => { setExitCloseReason(''); await queryClient.invalidateQueries({ queryKey: exitKey }); },
  });
  const bindingQuery = useQuery({
    queryKey: bindingKey,
    queryFn: ({ signal }) => currentCompany && investorId
      ? phase5Api.investorPortalBinding(currentCompany.id, investorId, signal)
      : Promise.reject(new Error('Select an Investor.')),
    enabled: Boolean(user && currentCompany && canReadConsolidated && investorId),
    retry: false,
  });
  const bindMutation = useMutation({
    mutationFn: () => currentCompany && user && investorId
      ? phase5Api.bindInvestorPortalAccount(currentCompany.id, user.id, investorId, portalLoginId)
      : Promise.reject(new Error('A verified Company and Investor are required.')),
    onSuccess: async () => {
      setPortalLoginId('');
      await queryClient.invalidateQueries({ queryKey: bindingKey });
    },
  });
  const revokeMutation = useMutation({
    mutationFn: () => currentCompany && user && bindingQuery.data
      ? phase5Api.revokeInvestorPortalBinding(currentCompany.id, user.id, bindingQuery.data.id, revokeReason)
      : Promise.reject(new Error('An active portal binding is required.')),
    onSuccess: async () => {
      setRevokeReason('');
      await queryClient.invalidateQueries({ queryKey: bindingKey });
    },
  });

  const refresh = () => {
    void investorsQuery.refetch();
    if (investorId) void projectionQuery.refetch();
    if (investorId) void bindingQuery.refetch();
    if (investorId) void exitQuery.refetch();
    if (activeExit) void settlementQuery.refetch();
  };

  const submitBinding = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (portalLoginId.trim()) bindMutation.mutate();
  };

  const submitRevocation = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (revokeReason.trim()) revokeMutation.mutate();
  };

  const submitReconciliation = (
    event: FormEvent<HTMLFormElement>,
    periodStart: string,
    sourceVersion: string | null,
  ) => {
    event.preventDefault();
    const reason = reconciliationReasons[investorId + ':' + periodStart]?.trim() ?? '';
    if (sourceVersion && reason.length >= 3 && !reconciliationMutation.isPending) {
      reconciliationMutation.mutate({
        period_start: periodStart,
        expected_source_version: sourceVersion,
        reason,
      });
    }
  };

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-3 pb-8" aria-label="Investor Profit review">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 pb-3 dark:border-zinc-800">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--theme-primary)]">Phase 8 · Source calculation</p>
          <h1 className="mt-1 text-xl font-extrabold text-gray-950 dark:text-white sm:text-2xl">Investor Profit period review</h1>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Confirmed Vehicle results grouped by the Investor’s Sale-date calendar.</p>
        </div>
        <button type="button" onClick={refresh} disabled={investorsQuery.isFetching || projectionQuery.isFetching} className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 text-xs font-bold disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900">
          <RefreshCw className={`h-3.5 w-3.5 ${investorsQuery.isFetching || projectionQuery.isFetching ? 'animate-spin' : ''}`} />Refresh
        </button>
      </header>

      {!canReadConsolidated ? (
        <Notice>This consolidated Investor calculation covers every Branch and is available only to a Company-level Accountant in this Company.</Notice>
      ) : investorsQuery.isPending ? (
        <p role="status" className="rounded-xl border border-gray-200 bg-white p-4 text-xs text-gray-500 dark:border-zinc-800 dark:bg-zinc-900">Loading Investor records…</p>
      ) : investorsQuery.isError ? (
        <Notice tone="error">Investor records could not be loaded. Refresh and verify your Company access.</Notice>
      ) : investorsQuery.data?.length === 0 ? (
        <Notice>No active Investor records are available for this Company.</Notice>
      ) : (
        <>
          <label className="max-w-lg text-xs font-bold text-gray-700 dark:text-gray-300">
            Investor
            <select value={investorId} disabled={extendNoticeMutation.isPending || cancellationReviewMutation.isPending} onChange={(event) => setInvestorId(event.target.value)} className="mt-1 h-9 w-full rounded-lg border border-gray-200 bg-white px-2.5 text-xs disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900">
              {(investorsQuery.data ?? []).map((investor) => <option key={investor.id} value={investor.id}>{investor.name}</option>)}
            </select>
          </label>

          <section className="rounded-xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900" aria-label="Investor portal access">
            <div className="mb-2"><h2 className="text-sm font-extrabold text-gray-950 dark:text-white">Investor Portal access</h2><p className="mt-1 text-[11px] text-gray-500">Link one verified Company login to this Investor. Passwords are never requested or shown.</p></div>
            {bindingQuery.isPending ? <p role="status" className="text-xs text-gray-500">Checking current access…</p> : bindingQuery.isError ? <p role="alert" className="text-xs text-red-700 dark:text-red-300">Portal access could not be checked. Refresh before changing it.</p> : bindingQuery.data ? (
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
                <div className="min-w-0 flex-1"><p className="text-xs font-bold">Active account: {bindingQuery.data.login_id}</p><p className="mt-0.5 text-[10px] text-gray-500">Linked {date(bindingQuery.data.effective_from.slice(0, 10))}</p></div>
                <form onSubmit={submitRevocation} className="flex flex-col gap-2 sm:flex-row sm:items-end">
                  <label className="text-[10px] font-bold text-gray-600 dark:text-gray-300">Reason to revoke<input value={revokeReason} onChange={(event) => setRevokeReason(event.target.value)} maxLength={500} required className="mt-1 h-9 w-full rounded-lg border border-gray-200 bg-white px-2.5 text-xs dark:border-zinc-700 dark:bg-zinc-900 sm:w-56" /></label>
                  <button type="submit" disabled={!revokeReason.trim() || revokeMutation.isPending} className="h-9 shrink-0 rounded-lg border border-red-300 px-3 text-xs font-bold text-red-700 disabled:opacity-50 dark:border-red-900 dark:text-red-300">{revokeMutation.isPending ? 'Revoking…' : 'Revoke access'}</button>
                </form>
              </div>
            ) : (
              <form onSubmit={submitBinding} className="flex flex-col gap-2 sm:flex-row sm:items-end">
                <label className="min-w-0 flex-1 text-[10px] font-bold text-gray-600 dark:text-gray-300">Verified login ID<input value={portalLoginId} onChange={(event) => setPortalLoginId(event.target.value)} autoComplete="off" maxLength={150} required className="mt-1 h-9 w-full rounded-lg border border-gray-200 bg-white px-2.5 text-xs dark:border-zinc-700 dark:bg-zinc-900" /></label>
                <button type="submit" disabled={!portalLoginId.trim() || bindMutation.isPending} className="h-9 shrink-0 rounded-lg bg-[#18181b] px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">{bindMutation.isPending ? 'Linking…' : 'Link Investor login'}</button>
              </form>
            )}
            {(bindMutation.error || revokeMutation.error) && <p role="alert" className="mt-2 text-xs text-red-700 dark:text-red-300">{(bindMutation.error || revokeMutation.error) instanceof Error ? (bindMutation.error || revokeMutation.error as Error).message : 'Portal access could not be changed.'}</p>}
          </section>

          <section className="rounded-xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900" aria-label="Investor Exit notice">
            <h2 className="text-sm font-extrabold text-gray-950 dark:text-white">Investor Exit notice</h2>
            {exitQuery.isPending ? <p role="status" className="mt-2 text-xs text-gray-500">Loading Exit requests…</p> : exitQuery.isError ? <p role="alert" className="mt-2 text-xs text-red-700 dark:text-red-300">Exit requests could not be loaded.</p> : !activeExit ? <p className="mt-2 text-xs text-gray-500">No open Exit request.</p> : <>
              <p className="mt-2 text-xs text-gray-600 dark:text-gray-300">{activeExit.status.replaceAll('_', ' ')} · Current deadline: {new Date(activeExit.notice_deadline).toLocaleString()}</p>
              {activeExit.status === 'CANCELLATION_PENDING' && <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-2.5 dark:border-amber-900 dark:bg-amber-950/30">
                <p className="text-xs font-bold text-amber-900 dark:text-amber-100">Investor requested cancellation</p>
                <p className="mt-1 text-[11px] text-amber-900 dark:text-amber-100">Investor's reason: {activeExit.cancellation_reason || 'Not provided'}</p>
                <label className="mt-2 block text-[10px] font-bold">Review note (optional)<input value={cancellationReviewReason} onChange={(event) => setCancellationReviewReason(event.target.value)} maxLength={500} className="mt-1 block h-9 w-full rounded-lg border border-amber-200 bg-white px-2 text-xs dark:border-amber-900 dark:bg-zinc-900" /></label>
                <div className="mt-2 flex flex-wrap gap-2"><button type="button" disabled={cancellationReviewMutation.isPending || extendNoticeMutation.isPending} onClick={() => cancellationReviewMutation.mutate(true)} className="h-9 rounded-lg bg-[#18181b] px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">Approve cancellation</button><button type="button" disabled={cancellationReviewMutation.isPending || extendNoticeMutation.isPending} onClick={() => cancellationReviewMutation.mutate(false)} className="h-9 rounded-lg border border-gray-300 px-3 text-xs font-bold disabled:opacity-50 dark:border-zinc-700">Keep Exit open</button></div>
                <p className="mt-1 text-[10px] text-amber-900 dark:text-amber-100">Approval cancels the Exit request. Neither option moves money.</p>
                {cancellationReviewMutation.error && <p role="alert" className="mt-1 text-xs text-red-700 dark:text-red-300">{cancellationReviewMutation.error instanceof Error ? cancellationReviewMutation.error.message : 'Cancellation review failed.'}</p>}
              </div>}
              <form className="mt-2 flex flex-wrap items-end gap-2" onSubmit={(event) => { event.preventDefault(); if (noticeDeadline && noticeReason.trim().length >= 3) extendNoticeMutation.mutate(); }}>
                <label className="text-[10px] font-bold">New deadline<input type="datetime-local" required value={noticeDeadline} onChange={(event) => setNoticeDeadline(event.target.value)} className="mt-1 block h-9 rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-900" /></label>
                <label className="min-w-40 flex-1 text-[10px] font-bold">Reason<input required minLength={3} maxLength={500} value={noticeReason} onChange={(event) => setNoticeReason(event.target.value)} className="mt-1 block h-9 w-full rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-900" /></label>
                <button type="submit" disabled={extendNoticeMutation.isPending || cancellationReviewMutation.isPending} className="h-9 rounded-lg bg-[#18181b] px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">{extendNoticeMutation.isPending ? 'Saving…' : 'Extend notice'}</button>
              </form>
              <p className="mt-1 text-[10px] text-gray-500">This records an extension; it does not settle the Exit or move money.</p>
              {extendNoticeMutation.error && <p role="alert" className="mt-1 text-xs text-red-700 dark:text-red-300">{extendNoticeMutation.error instanceof Error ? extendNoticeMutation.error.message : 'Notice extension failed.'}</p>}
              <div className="mt-3 rounded-lg border border-gray-200 p-2.5 dark:border-zinc-700" aria-label="Current Exit settlement review">
                <h3 className="text-xs font-extrabold">Current settlement review</h3>
                {settlementQuery.isPending ? <p role="status" className="mt-1 text-[11px] text-gray-500">Checking current fund, Vehicles and confirmed periods…</p> : settlementQuery.isError || !settlementQuery.data ? <p role="alert" className="mt-1 text-[11px] text-red-700 dark:text-red-300">Settlement sources could not be verified. No settlement was created.</p> : <>
                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
                    <p>Available principal: <strong>{settlementQuery.data.principal_available === null ? 'Needs review' : money(settlementQuery.data.principal_available)}</strong></p>
                    <p>Confirmed residual Loss: <strong>{money(settlementQuery.data.residual_confirmed_loss)}</strong></p>
                    <p>Vehicles reviewed: <strong>{settlementQuery.data.vehicles.length}</strong></p>
                  </div>
                  {settlementQuery.data.blockers.length ? <div className="mt-2 rounded-md bg-amber-50 p-2 text-[10px] text-amber-950 dark:bg-amber-950/30 dark:text-amber-100">
                    <p className="font-bold">Settlement is blocked until these positions are resolved:</p>
                    <ul className="mt-1 list-disc pl-4">{settlementQuery.data.blockers.map((blocker) => <li key={blocker}>{blocker.replaceAll('_', ' ')}</li>)}</ul>
                  </div> : <p className="mt-2 text-[10px] font-bold text-emerald-700 dark:text-emerald-300">Current sources are ready for authorized settlement review.</p>}
                  {settlementQuery.data.principal_available && Number(settlementQuery.data.principal_available) > 0 &&
                    settlementQuery.data.blockers.every((blocker) => blocker === 'EXIT_NOTICE_NOT_EXPIRED') && currentCompany && user &&
                    <InvestorExitPrincipalPaymentForm companyId={currentCompany.id} userId={user.id} investorId={investorId} position={settlementQuery.data}
                      onSaved={async () => { await settlementQuery.refetch(); }} />}
                  {settlementQuery.data.confirmed_losses.length > 0 && settlementQuery.data.blockers.every((blocker) => blocker === 'EXIT_NOTICE_NOT_EXPIRED') && currentCompany && user &&
                    <InvestorExitLossApplicationForm companyId={currentCompany.id} userId={user.id} investorId={investorId} position={settlementQuery.data}
                      onSaved={async () => { await settlementQuery.refetch(); }} />}
                  {settlementQuery.data.confirmed_positions.some((item) => item.kind === 'PAYABLE' && item.is_current && Number(item.amount) > 0) && settlementQuery.data.blockers.every((blocker) => blocker === 'EXIT_NOTICE_NOT_EXPIRED') && currentCompany && user &&
                    <InvestorExitProfitPaymentForm companyId={currentCompany.id} userId={user.id} investorId={investorId} position={settlementQuery.data}
                      onSaved={async () => { await settlementQuery.refetch(); }} />}
                  {!settlementQuery.data.blockers.length && settlementQuery.data.principal_available === '0.00' && Number(settlementQuery.data.residual_confirmed_loss) === 0 && settlementQuery.data.confirmed_positions.every((item) => item.kind === 'BALANCED' && Number(item.amount) === 0) && currentCompany && user &&
                    <form className="mt-2 flex flex-wrap items-end gap-2 border-t border-gray-200 pt-2 dark:border-zinc-700" onSubmit={(event) => { event.preventDefault(); if (exitCloseReason.trim().length >= 3) exitCloseMutation.mutate(); }}>
                      <label className="min-w-40 flex-1 text-[10px] font-bold">Final settlement reason<input required minLength={3} maxLength={500} value={exitCloseReason} onChange={(event) => setExitCloseReason(event.target.value)} className="mt-1 block h-9 w-full rounded-lg border border-gray-200 px-2 text-xs dark:border-zinc-700 dark:bg-zinc-900" /></label>
                      <button type="submit" disabled={exitCloseMutation.isPending} className="h-9 rounded-lg bg-[#18181b] px-3 text-xs font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black">{exitCloseMutation.isPending ? 'Closing…' : 'Close settled Exit'}</button>
                      {exitCloseMutation.error && <p role="alert" className="w-full text-xs text-red-700">{exitCloseMutation.error instanceof Error ? exitCloseMutation.error.message : 'Exit closure failed.'}</p>}
                    </form>}
                  <p className="mt-1 text-[10px] text-gray-500">Review order: {settlementQuery.data.settlement_order.join(' → ')}. Principal payment records only the actual partial payment; it does not close Exit.</p>
                </>}
              </div>
            </>}
          </section>

          {repayment && currentCompany && user && repayment.companyId === currentCompany.id && repayment.investorId === investorId &&
            <InvestorProfitRepaymentForm companyId={currentCompany.id} userId={user.id} investorId={investorId}
              position={repayment.position} onClose={() => setRepayment(null)} />}
          {futureAdjustment && currentCompany && user && futureAdjustment.companyId === currentCompany.id && futureAdjustment.investorId === investorId &&
            <InvestorProfitFutureAdjustmentForm companyId={currentCompany.id} userId={user.id} investorId={investorId}
              position={futureAdjustment.position} onClose={() => setFutureAdjustment(null)}
              targets={(projectionQuery.data?.periods ?? []).filter((period) =>
                period.period_start > futureAdjustment.periodEnd && period.confirmed_position?.is_current &&
                period.confirmed_position.kind === 'PAYABLE').flatMap((period) => period.future_profit_targets ?? [])} />}
          {projectionQuery.isPending ? (
            <p role="status" className="rounded-xl border border-gray-200 bg-white p-4 text-xs text-gray-500 dark:border-zinc-800 dark:bg-zinc-900">Calculating from confirmed Vehicle results…</p>
          ) : projectionQuery.isError || !projectionQuery.data ? (
            <Notice tone="error">The period calculation is unavailable. No payable or payment has been created.</Notice>
          ) : (
            <>
              <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-[11px] text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <p><strong>Calculation and source confirmation only.</strong> Confirming a period stores an audited calculation snapshot and any restatement difference. It does not create a payable, change Investor principal, post Cash/Bank, or mark Profit paid. Exit settlement and recovery remain separate workflows.</p>
              </div>

              <section className="rounded-xl border border-gray-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="text-sm font-extrabold text-gray-950 dark:text-white">Period calculation</h2>
                    <p className="mt-1 text-[11px] text-gray-500">Calendar: {projectionQuery.data.calendar.duration_months ?? '—'} months · Starts {date(projectionQuery.data.calendar.start_date)}</p>
                  </div>
                  <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-bold text-amber-900 dark:bg-amber-950 dark:text-amber-100">{projectionQuery.data.status.replaceAll('_', ' ')}</span>
                </div>
                {projectionQuery.data.periods.length === 0 ? (
                  <p className="py-4 text-xs text-gray-500">No complete period calculation is available.</p>
                ) : (
                  <div className="mt-2 overflow-x-auto">
                    <table className="w-full min-w-[850px] border-collapse text-left text-xs">
                      <thead><tr className="border-b border-gray-200 text-[10px] uppercase tracking-wide text-gray-500 dark:border-zinc-700"><th className="py-2 pr-3">Period</th><th className="py-2 pr-3">Gross Investor Profit</th><th className="py-2 pr-3">Deal Profit paid</th><th className="py-2 pr-3">Interim paid</th><th className="py-2 pr-3">Investor Loss share</th><th className="py-2 pr-3">Loss offset applied</th><th className="py-2 pr-3">Results</th><th className="py-2">Status</th></tr></thead>
                      <tbody>{projectionQuery.data.periods.map((period) => {
                        const reasonKey = investorId + ':' + period.period_start;
                        const canConfirm = Boolean(
                          period.source_version &&
                          projectionQuery.data.unassigned_result_count === 0 &&
                          ['NOT_RECONCILED', 'RESTATEMENT_REQUIRED'].includes(period.reconciliation_status),
                        );
                        return <tr key={period.period_start} className="border-b border-gray-100 align-top dark:border-zinc-800">
                          <td className="py-2 pr-3 font-semibold">{date(period.period_start)} – {date(period.period_end)}</td>
                          <td className="py-2 pr-3 tabular-nums">{money(period.gross_investor_profit)}</td>
                          <td className="py-2 pr-3 tabular-nums">{money(period.deal_profit_paid)}</td>
                          <td className="py-2 pr-3 tabular-nums">{money(period.interim_paid)}</td>
                          <td className="py-2 pr-3 tabular-nums">{money(period.investor_loss_share)}</td>
                          <td className="py-2 pr-3 tabular-nums">{money(period.loss_offset_applied)}</td>
                          <td className="py-2 pr-3 tabular-nums">{period.result_count}</td>
                          <td className="min-w-56 py-2 text-[10px]">
                            {period.reconciliation_status === 'RECONCILED' ? (
                              <div className="font-bold text-emerald-700 dark:text-emerald-300">
                                <p>RECONCILED · v{period.reconciliation_version}</p>
                                <p className="mt-1 font-normal text-gray-600 dark:text-gray-300">Position (not payable): {money(period.last_reconciled_net_position ?? '')}</p>
                                <p className="font-normal text-gray-600 dark:text-gray-300">Restatement: {money(period.last_restatement_adjustment ?? '')}</p>
                                {period.confirmed_position?.is_current ? (
                                  <div className="mt-1">
                                    <p>Confirmed {period.confirmed_position.kind.toLowerCase()}: {money(period.confirmed_position.amount)}</p>
                                    {period.confirmed_position.kind === 'RECOVERABLE' && <button type="button"
                                      onClick={() => setRepayment({ companyId: currentCompany!.id, investorId, position: period.confirmed_position! })}
                                      className="mt-1 h-8 rounded-lg border border-gray-200 px-2.5 text-[10px] dark:border-zinc-700">
                                      Record Investor repayment
                                    </button>}
                                    {period.confirmed_position.kind === 'RECOVERABLE' && <button type="button"
                                      onClick={() => setFutureAdjustment({ companyId: currentCompany!.id, investorId,
                                        position: period.confirmed_position!, periodEnd: period.period_end })}
                                      className="ml-1 mt-1 h-8 rounded-lg border border-gray-200 px-2.5 text-[10px] dark:border-zinc-700">
                                      Adjust against future Profit
                                    </button>}
                                  </div>
                                ) : (
                                  <form className="mt-2 flex flex-col gap-1.5" onSubmit={(event) => {
                                    event.preventDefault();
                                    if (period.reconciliation_id && period.source_version) positionMutation.mutate({
                                      reconciliation_id: period.reconciliation_id,
                                      expected_source_version: period.source_version,
                                      reason: positionReasons[reasonKey] ?? '',
                                    });
                                  }}>
                                    <input aria-label={'Position confirmation reason for ' + date(period.period_start)}
                                      value={positionReasons[reasonKey] ?? ''}
                                      onChange={(event) => setPositionReasons((current) => ({ ...current, [reasonKey]: event.target.value }))}
                                      className="h-9 rounded-lg border border-gray-200 px-2 text-xs font-normal dark:border-zinc-700 dark:bg-zinc-950"
                                      placeholder="Position confirmation reason" required minLength={3} maxLength={500} />
                                    <button type="submit" disabled={positionMutation.isPending || (positionReasons[reasonKey] ?? '').trim().length < 3 || projectionQuery.data.unassigned_result_count > 0}
                                      className="h-8 self-start rounded-lg bg-gray-900 px-2.5 text-[10px] text-white disabled:opacity-50 dark:bg-white dark:text-black">
                                      Confirm payable / recoverable
                                    </button>
                                  </form>
                                )}
                              </div>
                            ) : period.reconciliation_status === 'SOURCE_REVIEW_REQUIRED' ? (
                              <span className="font-bold text-amber-700 dark:text-amber-300">SOURCE REVIEW REQUIRED</span>
                            ) : (
                              <form onSubmit={(event) => submitReconciliation(event, period.period_start, period.source_version)}>
                                {period.reconciliation_status === 'RESTATEMENT_REQUIRED' && (
                                  <p className="mb-1 font-bold text-amber-700 dark:text-amber-300">
                                    RESTATEMENT REQUIRED · previous position {money(period.last_reconciled_net_position ?? '')} · change {money(period.pending_restatement_adjustment ?? '')}
                                  </p>
                                )}
                                {period.reconciliation_status === 'NOT_RECONCILED' && (
                                  <p className="mb-1 font-bold">NOT RECONCILED</p>
                                )}
                                <label className="block text-gray-600 dark:text-gray-300">
                                  <span className="sr-only">Reason for reconciliation starting {date(period.period_start)}</span>
                                  <input
                                    aria-label={'Reason for reconciliation starting ' + date(period.period_start)}
                                    value={reconciliationReasons[reasonKey] ?? ''}
                                    onChange={(event) => setReconciliationReasons((current) => ({ ...current, [reasonKey]: event.target.value }))}
                                    minLength={3}
                                    maxLength={500}
                                    required
                                    placeholder="Reason for review"
                                    className="h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-[10px] dark:border-zinc-700 dark:bg-zinc-950"
                                  />
                                </label>
                                <button
                                  type="submit"
                                  disabled={!canConfirm || (reconciliationReasons[reasonKey] ?? '').trim().length < 3 || reconciliationMutation.isPending}
                                  className="mt-1 h-8 rounded-md bg-[#18181b] px-2.5 text-[10px] font-bold text-white disabled:opacity-50 dark:bg-white dark:text-black"
                                >
                                  {reconciliationMutation.isPending && reconciliationMutation.variables?.period_start === period.period_start
                                    ? 'Saving…'
                                    : period.reconciliation_status === 'RESTATEMENT_REQUIRED' ? 'Confirm restatement' : 'Confirm period'}
                                </button>
                                {projectionQuery.data.unassigned_result_count > 0 && (
                                  <p className="mt-1 text-amber-700 dark:text-amber-300">Review unassigned results before confirming.</p>
                                )}
                              </form>
                            )}
                          </td>
                        </tr>;
                      })}</tbody>
                    </table>
                  </div>
                )}
                {positionMutation.error && <p role="alert" className="mt-2 text-xs text-red-700 dark:text-red-300">{positionMutation.error instanceof Error ? positionMutation.error.message : 'Position confirmation failed.'}</p>}
                {reconciliationMutation.error && <p role="alert" className="mt-2 text-xs text-red-700 dark:text-red-300">{reconciliationMutation.error instanceof Error ? reconciliationMutation.error.message : 'Period confirmation failed. No success was recorded.'}</p>}
                {projectionQuery.data.unassigned_result_count > 0 && <p className="mt-2 text-[11px] font-semibold text-amber-700 dark:text-amber-300">{projectionQuery.data.unassigned_result_count} result(s) need review and are excluded.</p>}
              </section>
            </>
          )}
        </>
      )}
    </main>
  );
};

function Notice({ children, tone = 'default' }: React.PropsWithChildren<{ tone?: 'default' | 'error' }>) {
  return <p role={tone === 'error' ? 'alert' : 'status'} className={`rounded-xl border px-3 py-3 text-xs ${tone === 'error' ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200' : 'border-gray-200 bg-white text-gray-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-gray-300'}`}>{children}</p>;
}
