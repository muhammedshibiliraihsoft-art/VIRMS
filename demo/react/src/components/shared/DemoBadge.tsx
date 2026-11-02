import React from 'react';

export type DemoBadgeSize = 'compact' | 'regular';

interface DemoBadgeProps {
  size?: DemoBadgeSize;
  className?: string;
}

const SIZE_CLASSES: Record<DemoBadgeSize, string> = {
  compact: 'px-1.5 py-0.5 text-[8px]',
  regular: 'px-2 py-0.5 text-[9px]',
};

/** Marks prototype data/actions that are not backed by a VIRMS business API. */
export const DemoBadge: React.FC<DemoBadgeProps> = ({
  size = 'regular',
  className = '',
}) => (
  <span
    role="note"
    aria-label="Demo data and actions; not connected to the backend"
    title="Demo data and actions are not saved to the VIRMS backend."
    data-demo-badge="true"
    className={`inline-flex shrink-0 items-center rounded-full border border-amber-500/20 bg-amber-500/10 font-extrabold leading-none tracking-wide text-amber-700 dark:text-amber-400 ${SIZE_CLASSES[size]} ${className}`}
  >
    Demo
  </span>
);
