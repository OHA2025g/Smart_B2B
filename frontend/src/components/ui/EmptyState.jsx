import { motion } from 'framer-motion';

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      {Icon && (
        <div className="rounded-2xl bg-teal-100 p-5 mb-4 text-teal-600">
          <Icon className="h-12 w-12" />
        </div>
      )}
      <h3 className="text-xl font-bold text-slate-900">{title}</h3>
      {description && <p className="mt-2 text-sm text-slate-500 max-w-sm">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </motion.div>
  );
}
