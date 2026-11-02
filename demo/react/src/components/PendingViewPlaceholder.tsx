import React from 'react';
import { ArrowLeft, Clock, ShieldCheck, Layers, FileText } from 'lucide-react';
import { navigationRegistry } from '../data/navigationRegistry';

interface PendingViewPlaceholderProps {
  routeKey: string;
  onReturnToDashboard: () => void;
  descriptionOverride?: string;
  stateOverride?: string;
}

export const PendingViewPlaceholder: React.FC<PendingViewPlaceholderProps> = ({
  routeKey,
  onReturnToDashboard,
  descriptionOverride,
  stateOverride,
}) => {
  // Find group and item from registry
  let foundGroup = navigationRegistry[0];
  let foundItem = foundGroup.children[0];

  for (const group of navigationRegistry) {
    const item = group.children.find((c) => c.routeKey === routeKey);
    if (item) {
      foundGroup = group;
      foundItem = item;
      break;
    }
  }

  const isReadOnly = foundItem.status === 'read_only_by_business_rule';

  return (
    <div className="flex-1 flex flex-col justify-center items-center py-12 px-6 text-center animate-in fade-in zoom-in-95 duration-150">
      <div className="max-w-lg w-full bg-[#f8f9fa] dark:bg-zinc-850/60 border border-gray-200/90 dark:border-zinc-700/70 rounded-[28px] p-8 shadow-xs flex flex-col items-center">

        {/* Top Badge Icon */}
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 shadow-xs ${
          isReadOnly
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400'
            : 'bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-400'
        }`}>
          {isReadOnly ? <ShieldCheck className="w-7 h-7" /> : <Clock className="w-7 h-7" />}
        </div>

        {/* Breadcrumb pill */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white dark:bg-zinc-800 border border-gray-200/80 dark:border-zinc-700 text-[11px] font-bold text-gray-500 dark:text-gray-400 mb-3">
          <span>{foundGroup.label}</span>
          <span>/</span>
          <span className="text-gray-900 dark:text-white">{foundItem.label}</span>
        </div>

        {/* Title & Description */}
        <h2 className="text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight">
          {foundItem.label}
        </h2>

        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 max-w-sm">
          {descriptionOverride || foundItem.description || 'This operational module is registered in the VIRMS navigation registry.'}
        </p>

        {/* Info Box */}
        <div className="w-full bg-white dark:bg-zinc-800/80 border border-gray-200/70 dark:border-zinc-700 rounded-2xl p-4 my-6 text-left text-xs space-y-2">
          <div className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
            <Layers className="w-4 h-4 text-[var(--theme-primary)] shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Navigation Route:</span>{' '}
              <code className="bg-gray-100 dark:bg-zinc-700 px-1.5 py-0.5 rounded text-[11px] font-mono">
                {foundItem.routeKey}
              </code>
            </div>
          </div>
          <div className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
            <FileText className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">State:</span>{' '}
              {stateOverride ? (
                <span className="text-gray-500 dark:text-gray-400">{stateOverride}</span>
              ) : isReadOnly ? (
                <span className="text-amber-600 dark:text-amber-400 font-semibold">
                  Read-only by business decision (V2 canonical requirement)
                </span>
              ) : (
                <span className="text-gray-500 dark:text-gray-400">
                  Registered in prototype navigation registry — scheduled for incremental integration
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Return Button */}
        <button
          onClick={onReturnToDashboard}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#18181b] hover:bg-black text-white font-bold text-xs shadow-xs transition cursor-pointer active:scale-[0.98]"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Dashboard Overview</span>
        </button>
      </div>
    </div>
  );
};
