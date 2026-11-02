import React, { useState } from 'react';
import { Search, SlidersHorizontal, MoreHorizontal } from 'lucide-react';
import { ActivityItem } from '../types';

interface RecentActivityTableProps {
  activities: ActivityItem[];
  onSelectActivity?: (item: ActivityItem) => void;
}

export const RecentActivityTable: React.FC<RecentActivityTableProps> = ({
  activities,
  onSelectActivity,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<string>('all');
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === activities.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(activities.map((a) => a.id));
    }
  };

  const filtered = activities.filter((act) => {
    const matchesQuery =
      act.code.toLowerCase().includes(query.toLowerCase()) ||
      act.title.toLowerCase().includes(query.toLowerCase()) ||
      act.subtitle.toLowerCase().includes(query.toLowerCase());

    const matchesFilter = filterType === 'all' || act.type === filterType;
    return matchesQuery && matchesFilter;
  });

  const formatCurrency = (val: number) =>
    '₹' + val.toLocaleString('en-IN');

  const renderStatus = (status: string, variant: string) => {
    let dotClass = 'bg-gray-400';
    let textClass = 'text-gray-700 dark:text-gray-300';

    if (variant === 'success') {
      dotClass = 'bg-emerald-500';
      textClass = 'text-emerald-700 dark:text-emerald-400';
    } else if (variant === 'warning') {
      dotClass = 'bg-amber-500';
      textClass = 'text-amber-700 dark:text-amber-400';
    } else if (variant === 'info') {
      dotClass = 'bg-blue-500';
      textClass = 'text-blue-700 dark:text-blue-400';
    }

    return (
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} />
        <span className={`text-[11px] font-semibold ${textClass}`}>{status}</span>
      </div>
    );
  };

  return (
    <div className="dashboard-card-solid rounded-[22px] p-4 sm:p-5 h-full flex flex-col justify-between">
      <div>
        {/* Table Header Controls */}
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-sm sm:text-base font-bold text-gray-950 dark:text-white">
            Recent Activities
          </h3>

          <div className="flex items-center gap-1.5">
            {/* Search Input Pill */}
            <div className="relative">
              <Search className="w-3 h-3 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-7 pr-2.5 py-1 rounded-full bg-white dark:bg-zinc-800 border border-[#f0eae4] dark:border-zinc-700 text-[11px] font-medium text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary-border)] focus:border-[var(--theme-primary)] w-28 sm:w-36 shadow-2xs transition"
              />
            </div>

            {/* Filter Button Pill */}
            <div className="relative">
              <button
                onClick={() => setShowFilterMenu(!showFilterMenu)}
                className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-white dark:bg-zinc-800 border border-[#f0eae4] dark:border-zinc-700 text-[11px] font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-700 shadow-2xs transition cursor-pointer"
              >
                <SlidersHorizontal className="w-3 h-3 text-gray-500" />
                <span>Filter</span>
              </button>

              {showFilterMenu && (
                <div className="absolute right-0 mt-1.5 w-36 bg-white dark:bg-zinc-900 rounded-xl shadow-xl border border-gray-100 dark:border-zinc-800 p-1 z-40 text-[11px] animate-in fade-in zoom-in-95 duration-100">
                  {['all', 'vehicle', 'job', 'sale'].map((t) => (
                    <button
                      key={t}
                      onClick={() => {
                        setFilterType(t);
                        setShowFilterMenu(false);
                      }}
                      className={`w-full text-left px-2.5 py-1 rounded-lg font-medium capitalize transition cursor-pointer ${
                        filterType === t
                          ? 'bg-gray-100 dark:bg-zinc-800 text-black dark:text-white font-bold'
                          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {t === 'all' ? 'All Activities' : `${t}s only`}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Responsive Table */}
        <div className="overflow-x-auto scrollbar-none">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#f0eae4] dark:border-zinc-800 text-[10px] font-semibold text-gray-400">
                <th className="py-2 px-1.5 w-7">
                  <input
                    type="checkbox"
                    aria-label="Select all"
                    checked={activities.length > 0 && selectedIds.length === activities.length}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300 text-gray-900 focus:ring-0 cursor-pointer w-3 h-3"
                  />
                </th>
                <th className="py-2 px-2.5 font-semibold">Order ID</th>
                <th className="py-2 px-2.5 font-semibold">Activity</th>
                <th className="py-2 px-2.5 font-semibold">Price</th>
                <th className="py-2 px-2.5 font-semibold">Status</th>
                <th className="py-2 px-2.5 font-semibold">Date</th>
                <th className="py-2 px-1 text-right"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3ece6] dark:divide-zinc-800 text-[11px]">
              {filtered.map((item) => {
                const isSelected = selectedIds.includes(item.id);
                return (
                  <tr
                    key={item.id}
                    onClick={() => onSelectActivity?.(item)}
                    className={`group transition-colors cursor-pointer ${
                      isSelected
                        ? 'bg-[var(--theme-primary-soft)]'
                        : 'hover:bg-white/80 dark:hover:bg-zinc-800/40'
                    }`}
                  >
                    <td
                      className="py-2.5 px-1.5"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSelect(item.id);
                      }}
                    >
                      <input
                        type="checkbox"
                        aria-label={`Select ${item.code}`}
                        checked={isSelected}
                        onChange={() => toggleSelect(item.id)}
                        className="rounded border-gray-300 text-gray-900 focus:ring-0 cursor-pointer w-3 h-3"
                      />
                    </td>

                    {/* Order ID */}
                    <td className="py-2.5 px-2.5 font-bold text-gray-950 dark:text-white whitespace-nowrap">
                      {item.code}
                    </td>

                    {/* Activity with Blue Icon Badge */}
                    <td className="py-2.5 px-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-md bg-blue-500 text-white flex items-center justify-center font-bold text-[10px] shrink-0 shadow-2xs">
                          {item.title.charAt(0)}
                        </div>
                        <div className="truncate max-w-[170px] sm:max-w-[210px]">
                          <span className="font-bold text-gray-900 dark:text-white">
                            {item.title}
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Price */}
                    <td className="py-2.5 px-2.5 font-extrabold text-gray-950 dark:text-white whitespace-nowrap">
                      {formatCurrency(item.amount)}
                    </td>

                    {/* Status */}
                    <td className="py-2.5 px-2.5 whitespace-nowrap">
                      {renderStatus(item.status, item.statusVariant)}
                    </td>

                    {/* Date */}
                    <td className="py-2.5 px-2.5 text-gray-500 dark:text-gray-400 whitespace-nowrap text-[10px]">
                      {item.date}
                    </td>

                    {/* More */}
                    <td className="py-2.5 px-1 text-right">
                      <button
                        aria-label="More"
                        className="p-0.5 rounded text-gray-400 hover:text-gray-600 transition cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreHorizontal className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
