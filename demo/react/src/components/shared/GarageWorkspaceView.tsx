import React, { useEffect, useState } from 'react';
import { useIsMutating, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { garageApi } from '../../api/garageApi';
import { hasCompanyBranchReadRole, useCompanyModuleStates } from '../../api/queries';
import { useAuth } from '../../auth/AuthContext';
import { GarageNewJob } from './GarageNewJob';
import { GarageCustomerFinance } from './GarageCustomerFinance';
import { LabourWorkspace } from './LabourWorkspace';
import { GarageStockCosts } from './GarageStockCosts';
import { GarageStatusHistory } from './GarageStatusHistory';
import { PageKpiRow } from './PageKpiRow';

/** Garage records are read from the Company API, never from the prototype dataset. */
const GarageJobsWorkspace: React.FC = () => {
  const { status, user, currentCompany } = useAuth();
  const queryClient = useQueryClient();
  const modules = useCompanyModuleStates();
  const companyId = currentCompany?.id ?? '';
  const userId = user?.id ?? '';
  const allowed = status === 'authenticated' && !!companyId && hasCompanyBranchReadRole(user);
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [workPage, setWorkPage] = useState(1);
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [financeBusy, setFinanceBusy] = useState(false);
  const canWrite = currentCompany?.roles.includes('accountant') && modules.isSuccess && modules.data.modules.some(row => row.code === 'garage' && row.state === 'enabled');

  useEffect(() => { setPage(1); setSelectedId(null); setWorkPage(1); setCreating(false); setFinanceBusy(false); }, [companyId, userId]);
  const jobs = useQuery({ queryKey: ['garage', userId, companyId, 'jobs', page], queryFn: ({ signal }) => garageApi.jobs(companyId, page, signal), enabled: allowed, retry: false });
  const jobSummary = useQuery({ queryKey: ['garage', userId, companyId, 'jobs', 'dashboard-summary'], queryFn: ({ signal }) => garageApi.jobSummary(companyId, undefined, signal), enabled: allowed && modules.isSuccess && modules.data.modules.some(row => row.code === 'garage' && row.state === 'enabled'), retry: false });
  const job = useQuery({ queryKey: ['garage', userId, companyId, 'job', selectedId], queryFn: ({ signal }) => garageApi.job(companyId, selectedId!, signal), enabled: allowed && !!selectedId, retry: false });
  const work = useQuery({ queryKey: ['garage', userId, companyId, 'work', selectedId, workPage], queryFn: ({ signal }) => garageApi.work(companyId, selectedId!, workPage, signal), enabled: allowed && !!selectedId, retry: false });
  const addWork = useMutation({ mutationFn: (text: string) => garageApi.addWork(companyId, userId, selectedId!, text), onSuccess: async () => { setDescription(''); await queryClient.invalidateQueries({ queryKey: ['garage', userId, companyId, 'work', selectedId] }); } });
  const changeStatus = useMutation({ mutationFn: () => garageApi.setStatus(companyId, userId, selectedId!, job.data!.status === 'OPEN' ? 'COMPLETED' : 'OPEN', job.data!.status_version), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['garage', userId, companyId] }); } });

  return <div className="space-y-4">
    <header><div className="text-[11px] font-bold tracking-wider text-[var(--theme-primary)] uppercase">Garage operations</div><h1 className="mt-0.5 text-xl font-extrabold text-gray-950 dark:text-white">Garage Jobs</h1><p className="text-xs text-gray-500">Company records</p></header>
    <PageKpiRow
      items={[
        { label: 'Total Jobs', value: String(jobSummary.data?.total_jobs ?? '—') },
        { label: 'Open', value: String(jobSummary.data?.open_jobs ?? '—') },
        { label: 'Completed', value: String(jobSummary.data?.completed_jobs ?? '—') },
        { label: 'External Customer Jobs', value: String(jobSummary.data?.external_customer_jobs ?? '—') },
      ]}
      status={modules.isLoading || jobSummary.isLoading ? 'loading' : !allowed || !modules.data?.modules.some(row => row.code === 'garage' && row.state === 'enabled') || jobSummary.isError || !jobSummary.data ? 'unavailable' : 'ready'}
    />
    {!allowed ? <p className="text-sm text-gray-500">A permitted Company account is required.</p> : <>
      {canWrite && !creating && <button type="button" disabled={financeBusy} onClick={() => setCreating(true)} className="rounded-full bg-[var(--theme-primary)] px-4 py-2 text-xs font-semibold text-white disabled:opacity-40">New job</button>}
      {canWrite && creating && <GarageNewJob companyId={companyId} userId={userId} onClose={() => setCreating(false)} onCreated={created => { setCreating(false); setPage(1); setWorkPage(1); setSelectedId(created.id); void queryClient.invalidateQueries({ queryKey: ['garage', userId, companyId, 'jobs'] }); }} />}
      {jobs.isPending && <p role="status" className="text-sm text-gray-500">Loading jobs…</p>}
      {jobs.isError && <p role="alert" className="text-sm text-red-600">Jobs could not be loaded. Please try again. <button type="button" onClick={() => void jobs.refetch()} className="underline">Retry</button></p>}
      {jobs.isSuccess && <section aria-label="Jobs" className="rounded-xl border border-gray-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        {jobs.data.results.length === 0 && <p className="p-4 text-sm text-gray-500">No jobs found.</p>}
        {jobs.data.results.map(row => <button type="button" key={row.id} disabled={financeBusy || addWork.isPending || changeStatus.isPending} onClick={() => { setSelectedId(row.id); setWorkPage(1); setDescription(''); addWork.reset(); changeStatus.reset(); }} className="flex w-full items-center justify-between gap-3 border-b border-gray-100 p-3 text-left last:border-0 hover:bg-gray-50 dark:border-zinc-800 dark:hover:bg-zinc-800">
          <span className="min-w-0"><span className="block truncate text-sm font-semibold">{row.vehicle_registration} · {row.vehicle_model}</span><span className="block text-xs text-gray-500">{row.branch_name} · {row.context === 'STOCK' ? 'Stock' : row.contact_name}</span></span><span className="shrink-0 text-xs font-semibold">{row.status === 'OPEN' ? 'Open' : 'Completed'}</span>
        </button>)}
        <div className="flex items-center justify-between gap-2 p-3 text-xs"><span>Page {page} · {jobs.data.count} jobs</span><span className="flex gap-3"><button type="button" disabled={!jobs.data.previous} onClick={() => setPage(p => p - 1)} className="disabled:opacity-40">Previous</button><button type="button" disabled={!jobs.data.next} onClick={() => setPage(p => p + 1)} className="disabled:opacity-40">Next</button></span></div>
      </section>}
      {selectedId && <section aria-label="Job details" className="space-y-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex justify-between gap-2"><h2 className="text-sm font-bold">Job details</h2><button type="button" disabled={financeBusy || addWork.isPending || changeStatus.isPending} onClick={() => setSelectedId(null)} className="text-xs">Close</button></div>
        {job.isPending && <p role="status" className="text-xs">Loading details…</p>}
        {job.isError && <p role="alert" className="text-xs text-red-600">Job details could not be loaded.</p>}
        {job.data && <><p className="text-sm font-semibold">{job.data.vehicle_registration} · {job.data.vehicle_model}</p><p className="text-xs text-gray-500">{job.data.branch_name} · {job.data.status === 'OPEN' ? 'Open' : 'Completed'}</p>{job.data.context === 'EXTERNAL_CUSTOMER' && <p className="text-xs">Customer: {job.data.contact_name}{job.data.contact_phone ? ` · ${job.data.contact_phone}` : ''}</p>}{job.data.customer_charge != null && <p className="text-xs">Charge ₹{job.data.customer_charge} · Received ₹{job.data.received} · Outstanding ₹{job.data.outstanding}</p>}</>}
        {job.data && <GarageStatusHistory key={`status-history-${job.data.id}`} companyId={companyId} userId={userId} jobId={job.data.id} />}
        <h3 className="text-xs font-bold">Work history</h3>
        {work.isPending && <p role="status" className="text-xs">Loading work…</p>}{work.isError && <p role="alert" className="text-xs text-red-600">Work history could not be loaded.</p>}
        {work.isSuccess && <><ul className="space-y-2 text-xs">{work.data.results.map(entry => <li key={entry.id}>{entry.description}</li>)}</ul>{work.data.results.length === 0 && <p className="text-xs text-gray-500">No work entries.</p>}<div className="flex gap-3 text-xs"><button type="button" disabled={!work.data.previous} onClick={() => setWorkPage(p => p - 1)} className="disabled:opacity-40">Previous</button><span>Page {workPage}</span><button type="button" disabled={!work.data.next} onClick={() => setWorkPage(p => p + 1)} className="disabled:opacity-40">Next</button></div></>}
        {canWrite && job.data && <><button type="button" disabled={financeBusy || changeStatus.isPending || addWork.isPending} onClick={() => changeStatus.mutate()} className="rounded border border-gray-300 px-3 py-2 text-xs disabled:opacity-40">{job.data.status === 'OPEN' ? 'Complete job' : 'Reopen job'}</button>{changeStatus.isError && <p role="alert" className="text-xs text-red-600">{changeStatus.error instanceof Error ? changeStatus.error.message : 'Status could not be changed.'}</p>}
          {job.data.status === 'OPEN' && <form onSubmit={event => { event.preventDefault(); if (description.trim() && !financeBusy && !changeStatus.isPending) addWork.mutate(description.trim()); }} className="flex flex-wrap gap-2"><label className="sr-only" htmlFor="garage-work">Work description</label><input id="garage-work" value={description} onChange={event => setDescription(event.target.value)} maxLength={500} required placeholder="Work description" className="min-w-0 flex-1 rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" /><button type="submit" disabled={financeBusy || addWork.isPending || changeStatus.isPending || !description.trim()} className="rounded bg-[var(--theme-primary)] px-3 py-2 text-xs text-white disabled:opacity-40">Add work</button></form>}{addWork.isError && <p role="alert" className="text-xs text-red-600">{addWork.error instanceof Error ? addWork.error.message : 'Work could not be added.'}</p>}</>}
        {job.data?.context === 'EXTERNAL_CUSTOMER' && <GarageCustomerFinance key={`customer-finance-${job.data.id}`} companyId={companyId} userId={userId} job={job.data} canWrite={!!canWrite} disabled={financeBusy || addWork.isPending || changeStatus.isPending} onBusyChange={setFinanceBusy} accountingEnabled={modules.isSuccess && modules.data.modules.some(row => row.code === 'accounting' && row.state === 'enabled')} />}
        {job.data?.context === 'STOCK' && <GarageStockCosts key={`stock-costs-${job.data.id}`} companyId={companyId} userId={userId} job={job.data} onBusyChange={setFinanceBusy} canWrite={!!canWrite && !addWork.isPending && !changeStatus.isPending && modules.isSuccess && modules.data.modules.some(row => row.code === 'vehicle_management' && row.state === 'enabled')} canChooseInvestor={!!currentCompany?.company_wide_roles.includes('accountant') && modules.isSuccess && modules.data.modules.some(row => row.code === 'investment' && row.state === 'enabled')} />}
      </section>}
    </>}
  </div>;
};

export const GarageWorkspaceView: React.FC = () => {
  const [view, setView] = useState<'jobs' | 'labour'>('jobs');
  const pendingMutations = useIsMutating();
  return <div className="space-y-4"><nav aria-label="Garage sections" className="flex gap-2 text-xs"><button type="button" disabled={pendingMutations > 0} aria-current={view === 'jobs' ? 'page' : undefined} onClick={() => setView('jobs')} className="rounded border border-gray-300 px-3 py-2 aria-[current=page]:font-bold disabled:opacity-40">Jobs</button><button type="button" disabled={pendingMutations > 0} aria-current={view === 'labour' ? 'page' : undefined} onClick={() => setView('labour')} className="rounded border border-gray-300 px-3 py-2 aria-[current=page]:font-bold disabled:opacity-40">Labour</button></nav>{view === 'jobs' ? <GarageJobsWorkspace /> : <LabourWorkspace />}</div>;
};
