import { motion } from 'framer-motion';

export function SkeletonCard() {
  return (
    <motion.div
      initial={{ opacity: 0.6 }}
      animate={{ opacity: 1 }}
      className="bg-white rounded-xl border border-neutral-200 overflow-hidden"
    >
      <div className="h-40 bg-neutral-200 animate-pulse" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-neutral-200 rounded w-3/4 animate-pulse" />
        <div className="h-3 bg-neutral-200 rounded w-1/2 animate-pulse" />
        <div className="h-4 bg-neutral-200 rounded w-1/3 animate-pulse" />
      </div>
    </motion.div>
  );
}

export function SkeletonLine({ className = '' }) {
  return <div className={`h-4 bg-neutral-200 rounded animate-pulse ${className}`} />;
}
