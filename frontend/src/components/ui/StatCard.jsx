import { motion } from 'framer-motion';

export function StatCard({ title, value, icon: Icon, trend, className = '', valueTitle, valueClassName = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white rounded-2xl border border-slate-200/90 p-5 shadow-md shadow-slate-200/40 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1 overflow-hidden">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
          <p
            className={`mt-2 font-bold tracking-tight text-slate-900 tabular-nums break-words ${valueClassName || 'text-2xl'}`}
            title={valueTitle || undefined}
          >
            {value}
          </p>
          {trend != null && (
            <p className={`mt-1 text-xs ${trend >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {trend >= 0 ? '+' : ''}
              {trend}% from last period
            </p>
          )}
        </div>
        {Icon && (
          <div className="rounded-xl bg-teal-50 p-2.5 text-teal-600 ring-1 ring-teal-100 shrink-0">
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </motion.div>
  );
}
