import React from 'react';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  Loader2,
  X,
} from 'lucide-react';
import { StatusMessage } from '../types/statusMessage';

interface StatusMessageLayerProps {
  messages: StatusMessage[];
  onDismiss: (id: string) => void;
}

export const StatusMessageLayer: React.FC<StatusMessageLayerProps> = ({
  messages,
  onDismiss,
}) => {
  if (messages.length === 0) return null;

  const getIcon = (type: StatusMessage['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />;
      case 'loading':
        return <Loader2 className="w-4 h-4 text-[var(--theme-primary)] animate-spin shrink-0" />;
      case 'info':
      default:
        return <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />;
    }
  };

  const getContainerStyles = (type: StatusMessage['type']) => {
    switch (type) {
      case 'success':
        return 'bg-emerald-50/95 dark:bg-emerald-950/80 border-emerald-200 dark:border-emerald-800/70 text-emerald-950 dark:text-emerald-200';
      case 'error':
        return 'bg-rose-50/95 dark:bg-rose-950/80 border-rose-200 dark:border-rose-800/70 text-rose-950 dark:text-rose-200';
      case 'warning':
        return 'bg-amber-50/95 dark:bg-amber-950/80 border-amber-200 dark:border-amber-800/70 text-amber-950 dark:text-amber-200';
      case 'loading':
        return 'bg-white/95 dark:bg-zinc-900/90 border-[var(--theme-primary-border)] text-gray-900 dark:text-white';
      case 'info':
      default:
        return 'bg-blue-50/95 dark:bg-blue-950/80 border-blue-200 dark:border-blue-800/70 text-blue-950 dark:text-blue-200';
    }
  };

  return (
    <div
      aria-live="polite"
      className="fixed bottom-5 right-5 sm:bottom-6 sm:right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
    >
      {messages.map((msg) => (
        <div
          key={msg.id}
          role={msg.type === 'error' ? 'alert' : 'status'}
          className={`pointer-events-auto flex items-start justify-between gap-3 p-3 rounded-2xl border shadow-xl backdrop-blur-md transition-all animate-in fade-in slide-in-from-bottom-2 duration-200 ${getContainerStyles(
            msg.type
          )}`}
        >
          <div className="flex items-start gap-2.5 min-w-0">
            <div className="pt-0.5">{getIcon(msg.type)}</div>
            <div className="min-w-0 text-xs">
              <div className="font-bold leading-tight truncate">{msg.message}</div>
              {msg.description && (
                <div className="text-[11px] opacity-80 mt-0.5 leading-normal">
                  {msg.description}
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => onDismiss(msg.id)}
            aria-label="Dismiss notification"
            className="p-1 -mr-1 -mt-0.5 rounded-lg opacity-60 hover:opacity-100 hover:bg-black/5 dark:hover:bg-white/10 transition cursor-pointer shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
