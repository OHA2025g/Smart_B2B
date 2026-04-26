const variants = {
  default: 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200/80',
  primary: 'bg-primary-100 text-primary-800 ring-1 ring-inset ring-primary-200/80',
  success: 'bg-emerald-100 text-emerald-800 ring-1 ring-inset ring-emerald-200/70',
  warning: 'bg-amber-100 text-amber-800 ring-1 ring-inset ring-amber-200/70',
  danger: 'bg-red-100 text-red-800 ring-1 ring-inset ring-red-200/70',
  outline: 'bg-white text-slate-600 ring-1 ring-inset ring-slate-300',
  teal: 'bg-teal-50 text-teal-800 ring-1 ring-inset ring-teal-200/80',
};

export function Badge({ children, variant = 'default', className = '' }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
