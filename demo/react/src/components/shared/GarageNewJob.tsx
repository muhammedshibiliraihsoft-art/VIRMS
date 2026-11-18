import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { garageApi, GarageJob } from '../../api/garageApi';
import { phase5Api, Phase5Vehicle } from '../../api/phase5Api';

interface Props { companyId: string; userId: string; onCreated: (job: GarageJob) => void; onClose: () => void }

export const GarageNewJob: React.FC<Props> = ({ companyId, userId, onCreated, onClose }) => {
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [vehicle, setVehicle] = useState<Phase5Vehicle | null>(null);
  const [context, setContext] = useState<'STOCK' | 'EXTERNAL_CUSTOMER'>('STOCK');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const vehicles = useQuery({ queryKey: ['garage', userId, companyId, 'vehicle-selection', search, page], queryFn: ({ signal }) => phase5Api.vehicles(companyId, { page, search }, signal), retry: false });
  const create = useMutation({ mutationFn: () => {
    if (!vehicle) throw new Error('Select a vehicle.');
    return garageApi.createJob(companyId, userId, { vehicle_id: vehicle.id, branch_id: vehicle.branch_id, context, contact_name: context === 'EXTERNAL_CUSTOMER' ? name.trim() : '', contact_phone: context === 'EXTERNAL_CUSTOMER' ? phone.trim() : '' });
  }, onSuccess: (job) => onCreated(job) });

  return <section aria-label="New Garage Job" className="space-y-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
    <div className="flex items-center justify-between gap-2"><h2 className="text-sm font-bold">New job</h2><button type="button" disabled={create.isPending} onClick={onClose} className="text-xs">Close</button></div>
    <fieldset disabled={create.isPending} className="space-y-3">
    <form onSubmit={event => { event.preventDefault(); setPage(1); setSearch(searchInput.trim()); }} className="flex gap-2"><label htmlFor="garage-vehicle-search" className="sr-only">Search vehicles</label><input id="garage-vehicle-search" value={searchInput} onChange={event => setSearchInput(event.target.value)} placeholder="Vehicle registration or model" className="min-w-0 flex-1 rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" /><button type="submit" className="rounded border border-gray-300 px-3 py-2 text-xs">Search</button></form>
    {vehicles.isPending && <p role="status" className="text-xs">Loading vehicles…</p>}
    {vehicles.isError && <p role="alert" className="text-xs text-red-600">Vehicles could not be loaded. <button type="button" onClick={() => void vehicles.refetch()} className="underline">Retry</button></p>}
    {vehicles.isSuccess && <><label htmlFor="garage-vehicle" className="block text-xs font-semibold">Vehicle</label><select id="garage-vehicle" value={vehicle && vehicles.data.results.some(row => row.id === vehicle.id) ? vehicle.id : ''} onChange={event => setVehicle(vehicles.data.results.find(row => row.id === event.target.value) ?? null)} className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900"><option value="">Select vehicle</option>{vehicles.data.results.map(row => <option key={row.id} value={row.id}>{row.registration} · {row.model} · {row.branch_name}</option>)}</select><div className="flex gap-3 text-xs"><button type="button" disabled={!vehicles.data.previous} onClick={() => setPage(p => p - 1)} className="disabled:opacity-40">Previous</button><span>Page {page}</span><button type="button" disabled={!vehicles.data.next} onClick={() => setPage(p => p + 1)} className="disabled:opacity-40">Next</button></div></>}
    {vehicle && <p className="text-xs">Selected: <strong>{vehicle.registration} · {vehicle.model}</strong> — {vehicle.branch_name}</p>}
    <form onSubmit={event => { event.preventDefault(); if (vehicle && (context !== 'EXTERNAL_CUSTOMER' || name.trim())) create.mutate(); }} className="space-y-3">
      <label className="block text-xs font-semibold" htmlFor="garage-context">Job type</label><select id="garage-context" value={context} onChange={event => setContext(event.target.value as typeof context)} className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900"><option value="STOCK">Stock vehicle</option><option value="EXTERNAL_CUSTOMER">External customer</option></select>
      {context === 'EXTERNAL_CUSTOMER' && <><label className="block text-xs font-semibold" htmlFor="garage-customer-name">Customer name</label><input id="garage-customer-name" value={name} onChange={event => setName(event.target.value)} maxLength={160} required className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" /><label className="block text-xs font-semibold" htmlFor="garage-customer-phone">Phone (optional)</label><input id="garage-customer-phone" value={phone} onChange={event => setPhone(event.target.value)} maxLength={40} className="w-full rounded border border-gray-300 px-3 py-2 text-xs dark:bg-zinc-900" /></>}
      {create.isError && <p role="alert" className="text-xs text-red-600">{create.error instanceof Error ? create.error.message : 'Job could not be saved.'}</p>}
      <button type="submit" disabled={!vehicle || create.isPending} className="rounded bg-[var(--theme-primary)] px-3 py-2 text-xs text-white disabled:opacity-40">{create.isPending ? 'Saving…' : 'Save job'}</button>
    </form></fieldset>
  </section>;
};
