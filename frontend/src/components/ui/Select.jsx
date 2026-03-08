import { forwardRef } from 'react';

export const Select = forwardRef(
  ({ className = '', error, label, options = [], placeholder, ...props }, ref) => (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-neutral-700 mb-1">{label}</label>
      )}
      <select
        ref={ref}
        className={`w-full border rounded-lg px-3 py-2 text-neutral-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
          error ? 'border-red-500' : 'border-neutral-300'
        } ${className}`}
        {...props}
      >
        {placeholder && (
          <option value="">{placeholder}</option>
        )}
        {options.map((opt) =>
          typeof opt === 'object' ? (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ) : (
            <option key={opt} value={opt}>{opt}</option>
          )
        )}
      </select>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  )
);
Select.displayName = 'Select';
