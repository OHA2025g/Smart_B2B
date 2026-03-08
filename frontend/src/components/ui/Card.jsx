import { motion } from 'framer-motion';

export function Card({ children, className = '', hover = false, ...props }) {
  const Comp = motion.div;
  return (
    <Comp
      className={`bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden ${className}`}
      initial={false}
      whileHover={hover ? { y: -2, boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' } : undefined}
      transition={{ duration: 0.2 }}
      {...props}
    >
      {children}
    </Comp>
  );
}

export function CardHeader({ children, className = '' }) {
  return <div className={`px-5 py-4 border-b border-neutral-100 ${className}`}>{children}</div>;
}

export function CardBody({ children, className = '' }) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return <div className={`px-5 py-4 bg-neutral-50 border-t border-neutral-100 ${className}`}>{children}</div>;
}
