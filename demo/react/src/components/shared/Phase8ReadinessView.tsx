import React from 'react';
import { AlertTriangle } from 'lucide-react';

type Props = { routeKey: 'Reconciliation & Settlement' | 'Owner Distribution' };

const copy = {
  'Reconciliation & Settlement': {
    title: 'Investor reconciliation and settlement',
    summary: 'Investor Profit period calculations are available for review, but the confirmed reconciliation and final settlement workflow is not yet implemented.',
    items: [
      'A calculated period amount is not a payable, recovery, or Paid amount.',
      'Investor Exit request and cancellation records do not themselves close settlement or move money.',
      'No principal, Profit, Interim, or settlement payment can be posted from this page.',
    ],
  },
  'Owner Distribution': {
    title: 'Owner Distribution',
    summary: 'The Company Result page shows an Accounting Income-minus-Expense view only; it is not the confirmed distributable Company Profit.',
    items: [
      'Company period confirmation, protected recipient split snapshots, Owner allocations, and actual partial payouts are not yet available here.',
      'A period end or Accounting Result does not authorize an Owner payment.',
      'No Owner distribution or Cash/Bank movement is created from this page.',
    ],
  },
} satisfies Record<Props['routeKey'], { title: string; summary: string; items: string[] }>;

export const Phase8ReadinessView: React.FC<Props> = ({ routeKey }) => {
  const content = copy[routeKey];
  return (
    <main className="mx-auto w-full max-w-4xl space-y-3 pb-8" aria-label={content.title}>
      <header className="border-b border-gray-200 pb-3 dark:border-zinc-800">
        <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--theme-primary)]">Phase 8 · Not complete</p>
        <h1 className="mt-1 text-xl font-extrabold text-gray-950 dark:text-white sm:text-2xl">{content.title}</h1>
      </header>
      <section className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100" role="status">
        <div className="flex items-start gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><div className="min-w-0"><p className="font-bold">{content.summary}</p><ul className="mt-2 list-disc space-y-1 pl-4">{content.items.map((item) => <li key={item}>{item}</li>)}</ul></div></div>
      </section>
    </main>
  );
};
