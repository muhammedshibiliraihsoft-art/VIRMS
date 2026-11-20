import React from 'react';
import { CheckCircle2 } from 'lucide-react';

type Props = { routeKey: 'Reconciliation & Settlement' | 'Owner Distribution' };

const copy = {
  'Reconciliation & Settlement': {
    title: 'Investor reconciliation and settlement',
    summary: 'Use the Investor Profit review and Exit settlement screens to work from current confirmed positions and recorded Accounting movements.',
    items: [
      'Only current Accountant-confirmed positions become payable or recoverable; calculations remain review data until confirmed.',
      'Exit settlement enforces principal, residual Loss, then remaining Profit order and keeps unresolved source blockers visible.',
      'Actual payments, repayments, future adjustments and Exit movements are posted once through the existing Accounting flow.',
    ],
  },
  'Owner Distribution': {
    title: 'Owner Distribution',
    summary: 'Company Result now combines the source Accounting report with Accountant-confirmed period distribution and partial Owner payout review.',
    items: [
      'Accounting Result is not distributable by itself; the Accountant must confirm liabilities, carryforward and the distributable amount.',
      'Confirmed Owner percentage snapshots and paise-exact allocations are retained per Company period version.',
      'Partial Owner payouts require a current confirmation and create one typed Accounting movement each.',
    ],
  },
} satisfies Record<Props['routeKey'], { title: string; summary: string; items: string[] }>;

export const Phase8ReadinessView: React.FC<Props> = ({ routeKey }) => {
  const content = copy[routeKey];
  return (
    <main className="mx-auto w-full max-w-4xl space-y-3 pb-8" aria-label={content.title}>
      <header className="border-b border-gray-200 pb-3 dark:border-zinc-800">
      <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--theme-primary)]">Phase 8 · Current workflow</p>
        <h1 className="mt-1 text-xl font-extrabold text-gray-950 dark:text-white sm:text-2xl">{content.title}</h1>
      </header>
      <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100" role="status">
        <div className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" /><div className="min-w-0"><p className="font-bold">{content.summary}</p><ul className="mt-2 list-disc space-y-1 pl-4">{content.items.map((item) => <li key={item}>{item}</li>)}</ul></div></div>
      </section>
    </main>
  );
};
