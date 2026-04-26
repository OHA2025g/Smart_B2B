import { motion } from 'framer-motion';

export function EmptyState({ icon: Icon, title, description, action, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex flex-col items-center justify-center py-14 px-6 text-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 ${className}`}
    >
      {Icon && (
        <div className="rounded-2xl bg-white p-5 mb-5 text-teal-600 shadow-md shadow-slate-200/50 ring-1 ring-slate-100">
          <Icon className="h-11 w-11" />
        </div>
      )}
      <h3 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h3>
      {description && (
        <div className="mt-2 text-sm text-slate-500 max-w-md leading-relaxed w-full [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:text-left space-y-2">
          {description}
        </div>
      )}
      {action && <div className="mt-5">{action}</div>}
    </motion.div>
  );
}
