import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { garageApi } from '../../api/garageApi';

export const GarageStatusHistory: React.FC<{ companyId: string; userId: string; jobId: string }> = ({ companyId, userId, jobId }) => {
  const [expanded, setExpanded] = useState(false);
  const [page, setPage] = useState(1);
  const history = useQuery({ queryKey: ['garage', userId, companyId, 'status-history', jobId, page], queryFn: ({ signal }) => garageApi.statusHistory(companyId, jobId, page, signal), enabled: expanded, retry: false });
  return <section className="space-y-2"><button type="button" aria-expanded={expanded} onClick={() => setExpanded(value => !value)} className="rounded border border-gray-300 px-3 py-2 text-xs">{expanded ? 'Hide status history' : 'Show status history'}</button>
    {expanded && <div aria-label="Status history" className="space-y-2 text-xs">{history.isPending && <p role="status">Loading status history…</p>}{history.isError && <p role="alert" className="text-red-600">Status history could not be loaded. <button type="button" className="underline" onClick={() => void history.refetch()}>Retry</button></p>}{history.isSuccess && <>{history.data.results.length === 0 && <p className="text-gray-500">No status changes.</p>}<ol className="space-y-1">{history.data.results.map(row => <li key={row.version}>{row.from_status === 'OPEN' ? 'Open' : 'Completed'} → {row.to_status === 'OPEN' ? 'Open' : 'Completed'} · {new Date(row.created_at).toLocaleString()}</li>)}</ol><div className="flex gap-3"><button type="button" disabled={!history.data.previous} onClick={() => setPage(p => p - 1)} className="disabled:opacity-40">Previous</button><span>Page {page}</span><button type="button" disabled={!history.data.next} onClick={() => setPage(p => p + 1)} className="disabled:opacity-40">Next</button></div></>}</div>}
  </section>;
};
