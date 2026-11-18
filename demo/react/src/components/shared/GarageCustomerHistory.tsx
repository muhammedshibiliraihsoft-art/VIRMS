import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { garageApi } from '../../api/garageApi';
import { GarageReceiptCorrection } from './GarageReceiptCorrection';

type HistoryKind = 'charges' | 'receipts' | 'cost';
interface Props { companyId: string; userId: string; jobId: string; kind: HistoryKind; costId?: string; canCorrect?: boolean; disabled?: boolean; onBusyChange?: (busy: boolean) => void; onClose: () => void }

export const GarageCustomerHistory: React.FC<Props> = ({ companyId, userId, jobId, kind, costId, canCorrect = false, disabled = false, onBusyChange, onClose }) => {
  const [page, setPage] = useState(1);
  const history = useQuery({
    queryKey: ['garage', userId, companyId, 'history', jobId, kind, costId, page],
    queryFn: async ({ signal }) => {
      if (kind === 'charges') return garageApi.charges(companyId, jobId, page, signal);
      if (kind === 'receipts') return garageApi.receipts(companyId, jobId, page, signal);
      if (!costId) throw new Error('Cost is required.');
      return garageApi.customerCostHistory(companyId, jobId, costId, page, signal);
    }, retry: false,
  });
  return <section aria-label="Record history" className="space-y-2 rounded border border-gray-200 p-3 dark:border-zinc-800">
    <div className="flex justify-between gap-2"><h4 className="text-xs font-bold">{kind === 'charges' ? 'Charge history' : kind === 'receipts' ? 'Receipt history' : 'Cost correction history'}</h4><button type="button" disabled={disabled} onClick={onClose} className="text-xs">Close history</button></div>
    {history.isPending && <p role="status" className="text-xs">Loading history…</p>}
    {history.isError && <p role="alert" className="text-xs text-red-600">History could not be loaded. <button type="button" onClick={() => void history.refetch()} className="underline">Retry</button></p>}
    {history.isSuccess && <>{history.data.results.length === 0 && <p className="text-xs text-gray-500">No history records.</p>}<ul className="space-y-3 text-xs">{history.data.results.map(row => <li key={row.id} className="space-y-2">{'reference' in row ? <><span>{row.is_void ? 'Voided receipt' : `₹${row.amount}`} · {row.reference} · {new Date(row.effective_at).toLocaleString()}</span><GarageReceiptCorrection companyId={companyId} userId={userId} jobId={jobId} receipt={row} canCorrect={canCorrect} disabled={disabled} onBusyChange={onBusyChange ?? (() => {})} /></> : <span>₹{row.amount} · Version {row.version} · {new Date(row.created_at).toLocaleString()}{row.reason ? ` · ${row.reason}` : ''}</span>}</li>)}</ul><div className="flex gap-3 text-xs"><button type="button" disabled={disabled || !history.data.previous} onClick={() => setPage(p => p - 1)} className="disabled:opacity-40">Previous</button><span>Page {page}</span><button type="button" disabled={disabled || !history.data.next} onClick={() => setPage(p => p + 1)} className="disabled:opacity-40">Next</button></div></>}
  </section>;
};
