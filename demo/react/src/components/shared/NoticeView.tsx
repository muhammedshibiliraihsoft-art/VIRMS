import React from 'react';
import { AlertCircle, FileText, ArrowRight, ShieldAlert, Lock } from 'lucide-react';

interface NoticeViewProps {
  title: string;
  category: string;
  bdrCodes: string[];
  description: string;
  reasons: string[];
  canonicalReference?: string;
  onExploreReports?: () => void;
}

export const NoticeView: React.FC<NoticeViewProps> = ({
  title,
  category,
  bdrCodes,
  description,
  reasons,
  canonicalReference = '/docs-final-v2/01-business-rules.md',
  onExploreReports,
}) => {
  return (
    <div className="space-y-5 animate-in fade-in duration-150">
      {/* Top Banner / Heading */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#f2ebe5] dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--theme-primary)]">
            {category} · GOVERNANCE NOTICE
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-gray-950 dark:text-white tracking-tight mt-0.5">
            {title}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-medium">
            Read-only notice view pursuant to VIRMS V2 canonical specification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs font-semibold">
            <Lock className="w-3.5 h-3.5" />
            <span>BUSINESS DECISION REQUIRED</span>
          </span>
        </div>
      </div>

      {/* Primary Formal Notice Card */}
      <div className="dashboard-card-solid rounded-[24px] p-6 sm:p-8 space-y-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h2 className="text-base sm:text-lg font-bold text-gray-950 dark:text-white">
              Canonical Specification Lock
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
              {description}
            </p>
          </div>
        </div>

        {/* Governed Decision Items */}
        <div className="space-y-3">
          <div className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
            Unresolved Canonical Invariants ({bdrCodes.join(', ')})
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {reasons.map((reason, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-gray-50/70 dark:bg-zinc-800/40 border border-[#ebe2d8] dark:border-zinc-800 flex items-start gap-2.5"
              >
                <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <span className="text-xs text-gray-700 dark:text-gray-300 font-medium leading-normal">
                  {reason}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Canonical Policy Safeguard */}
        <div className="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
            <span className="text-xs font-semibold text-blue-900 dark:text-blue-200">
              Authority reference: <code className="font-mono">{canonicalReference}</code>
            </span>
          </div>
          {onExploreReports && (
            <button
              onClick={onExploreReports}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-zinc-800 text-xs font-bold text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-zinc-700 hover:bg-gray-50 transition cursor-pointer shadow-2xs"
            >
              <span>View operational reports</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
