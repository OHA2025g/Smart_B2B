import { motion } from 'framer-motion';

export function StatCard({ title, value, icon: Icon, trend, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white rounded-xl border border-neutral-200 p-5 shadow-sm ${className}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-neutral-500">{title}</p>
          <p className="mt-1 text-2xl font-semibold text-neutral-900">{value}</p>
          {trend != null && (
            <p className={`mt-1 text-xs ${trend >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {trend >= 0 ? '+' : ''}{trend}% from last period
            </p>
          )}
        </div>
        {Icon && (
          <div className="rounded-lg bg-primary-100 p-2 text-primary-600">
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </motion.div>
  );
}
