import React from 'react';

export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Top Row Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-28 rounded-[22px] bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5 p-4 flex flex-col justify-between"
          >
            <div className="w-24 h-3 rounded bg-black/10 dark:bg-white/10" />
            <div className="w-32 h-7 rounded bg-black/10 dark:bg-white/10" />
            <div className="w-16 h-2.5 rounded bg-black/10 dark:bg-white/10" />
          </div>
        ))}
      </div>

      {/* Middle Row Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        <div className="lg:col-span-7 h-72 rounded-[22px] bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5 p-5" />
        <div className="lg:col-span-5 h-72 rounded-[22px] bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5 p-5" />
      </div>

      {/* Bottom Row Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="h-56 rounded-[22px] bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5 p-4" />
        <div className="h-56 rounded-[22px] bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5 p-4" />
        <div className="h-56 rounded-[22px] bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5 p-4" />
      </div>
    </div>
  );
};
