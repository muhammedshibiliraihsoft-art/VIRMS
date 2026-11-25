import React from 'react';

export interface PageKpiItem {
  label: string;
  value: string;
}

interface PageKpiRowProps {
  items: PageKpiItem[];
  status: 'loading' | 'unavailable' | 'ready';
}

export const PageKpiRow: React.FC<PageKpiRowProps> = ({ items, status }) => {
  if (items.length < 3 || items.length > 4) {
    throw new Error('A page KPI row requires three or four items.');
  }

  const gridColumns = items.length === 3 ? 'lg:grid-cols-3' : 'lg:grid-cols-4';
  const valueFor = (value: string) => status === 'loading'
    ? 'Loading…'
    : status === 'unavailable'
      ? 'Unavailable'
      : value;

  return (
    <section aria-label="Page key metrics" className={`grid grid-cols-1 gap-2.5 sm:grid-cols-2 ${gridColumns}`}>
      {items.map((item, index) => (
        <article
          key={item.label}
          className={index === 0
            ? 'dashboard-card-orange flex min-h-[76px] min-w-0 flex-col justify-between rounded-2xl p-3.5 text-white sm:p-4'
            : 'dashboard-card-solid flex min-h-[76px] min-w-0 flex-col justify-between rounded-2xl p-3.5 sm:p-4'}
          aria-label={`${item.label}: ${valueFor(item.value)}`}
        >
          <span className={index === 0
            ? 'text-[10px] font-bold uppercase tracking-wide text-white/90'
            : 'text-[10px] font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400'}>
            {item.label}
          </span>
          <span className={index === 0
            ? 'mt-1 truncate text-xl font-extrabold tabular-nums text-white sm:text-2xl'
            : 'mt-1 truncate text-xl font-extrabold tabular-nums text-gray-950 dark:text-white sm:text-2xl'}
            role={status === 'loading' ? 'status' : undefined}
          >
            {valueFor(item.value)}
          </span>
        </article>
      ))}
    </section>
  );
};

export default PageKpiRow;
