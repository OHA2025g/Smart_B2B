import { motion } from 'framer-motion';

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      {Icon && (
        <div className="rounded-full bg-neutral-100 p-4 mb-4 text-neutral-400">
          <Icon className="h-10 w-10" />
        </div>
      )}
      <h3 className="text-lg font-medium text-neutral-900">{title}</h3>
      {description && <p className="mt-1 text-sm text-neutral-500 max-w-sm">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </motion.div>
  );
}
