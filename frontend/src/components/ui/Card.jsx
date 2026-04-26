import { motion } from 'framer-motion';

export function Card({ children, className = '', hover = false, ...props }) {
  const Comp = motion.div;
  return (
    <Comp
      className={`bg-white rounded-2xl border border-slate-200 shadow-lg shadow-slate-200/30 overflow-hidden hover:border-teal-200/80 ${className}`}
      initial={false}
      whileHover={hover ? { y: -6, boxShadow: '0 24px 48px -16px rgb(0 0 0 / 0.14)', transition: { duration: 0.2 } } : undefined}
      transition={{ duration: 0.2 }}
      {...props}
    >
      {children}
    </Comp>
  );
}

export function CardHeader({ children, className = '' }) {
  return <div className={`px-5 py-4 border-b border-slate-100 bg-slate-50/40 ${className}`}>{children}</div>;
}

export function CardBody({ children, className = '' }) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return <div className={`px-5 py-4 bg-slate-50/80 border-t border-slate-100 ${className}`}>{children}</div>;
}
