/**
 * Returns a placeholder "image" (gradient + label) config for a category.
 * Used for product cards and detail gallery when no real image exists.
 */
const categoryGradients = {
  Industrial: 'from-slate-600 to-slate-800',
  Textiles: 'from-amber-500 to-orange-600',
  Electronics: 'from-blue-500 to-indigo-600',
  Agriculture: 'from-emerald-500 to-teal-600',
  Chemicals: 'from-violet-500 to-purple-600',
  Machinery: 'from-neutral-600 to-neutral-800',
  Construction: 'from-amber-600 to-yellow-700',
  Automotive: 'from-red-600 to-rose-700',
  Pharmaceuticals: 'from-sky-500 to-blue-600',
  'Food & Beverage': 'from-orange-500 to-red-500',
  Plastics: 'from-cyan-500 to-blue-600',
  Paper: 'from-stone-500 to-neutral-600',
  default: 'from-primary-600 to-primary-800',
};

export function getCategoryImage(category) {
  const key = category && categoryGradients[category] ? category : 'default';
  return {
    gradient: categoryGradients[key] || categoryGradients.default,
    label: category || 'Product',
  };
}

export default getCategoryImage;
