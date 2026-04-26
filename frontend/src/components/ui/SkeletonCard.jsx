import { motion } from 'framer-motion';

export function SkeletonCard() {
  return (
    <motion.div
      initial={{ opacity: 0.7 }}
      animate={{ opacity: 1 }}
      className="bg-white rounded-2xl border border-slate-200/90 shadow-md shadow-slate-200/40 overflow-hidden"
    >
      <div className="h-48 bg-gradient-to-r from-slate-100 via-white to-slate-100 bg-[length:200%_100%] animate-shimmer" />
      <div className="p-5 space-y-3">
        <div className="h-4 bg-slate-200 rounded-lg w-4/5 animate-pulse" />
        <div className="h-3 bg-slate-100 rounded-lg w-3/5 animate-pulse" />
        <div className="flex gap-2 pt-1">
          <div className="h-6 bg-slate-100 rounded-full w-16 animate-pulse" />
          <div className="h-6 bg-slate-100 rounded-full w-20 animate-pulse" />
        </div>
        <div className="h-9 bg-slate-100 rounded-xl w-full animate-pulse mt-2" />
      </div>
    </motion.div>
  );
}

export function SkeletonLine({ className = '' }) {
  return <div className={`h-4 bg-neutral-200 rounded animate-pulse ${className}`} />;
}
