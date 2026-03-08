/**
 * Returns a placeholder "image" (gradient + label) config for a category.
 * Used for product cards and detail gallery when no real image exists.
 */
const categoryGradients = {
  Industrial: 'from-slate-600 to-slate-800',
  Textiles: 'from-amber-500 to-orange-600',
  Electronics: 'from-blue-600 to-indigo-700',
  Agriculture: 'from-emerald-600 to-teal-700',
  Chemicals: 'from-violet-600 to-purple-700',
  Machinery: 'from-neutral-600 to-neutral-800',
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
