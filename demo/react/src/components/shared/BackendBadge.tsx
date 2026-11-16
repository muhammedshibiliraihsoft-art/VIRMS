import React from 'react';

/** Marks a workspace whose business records are read and saved through the VIRMS API. */
export const BackendBadge: React.FC = () => (
  <span
    role="note"
    aria-label="Backend API data and actions"
    title="This workspace reads and saves records through the VIRMS backend API."
    data-backend-badge="true"
    className="inline-flex shrink-0 items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[9px] font-extrabold leading-none tracking-wide text-emerald-700 dark:text-emerald-400"
  >
    Backend API
  </span>
);
