import { forwardRef } from 'react';
import { motion } from 'framer-motion';

const variants = {
  primary: 'bg-teal-600 text-white hover:bg-teal-700 shadow-sm hover:shadow-glow transition-shadow',
  secondary: 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400',
  ghost: 'text-slate-700 hover:bg-slate-100',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  outlineDanger:
    'bg-white border-2 border-red-200 text-red-700 hover:bg-red-50 hover:border-red-300 shadow-sm',
  successSolid:
    'bg-emerald-600 text-white hover:bg-emerald-700 border-0 shadow-sm',
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm rounded-md',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-6 py-3 text-base rounded-lg',
};

export const Button = forwardRef(
  ({ children, variant = 'primary', size = 'md', className = '', disabled, ...props }, ref) => {
    const Comp = motion.button;
    return (
      <Comp
        ref={ref}
        type="button"
        className={`inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ${variants[variant]} ${sizes[size]} ${className}`}
        disabled={disabled}
        whileHover={disabled ? {} : { scale: 1.02 }}
        whileTap={disabled ? {} : { scale: 0.98 }}
        {...props}
      >
        {children}
      </Comp>
    );
  }
);
Button.displayName = 'Button';
