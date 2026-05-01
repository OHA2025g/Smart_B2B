import { Badge } from './ui/Badge';
import { Sparkles } from 'lucide-react';

/** Plan and verification are separate. Pass seller-ish object with subscriptionPlan, isFeaturedSupplier, isVerifiedSupplier, searchBoostLabel */
export function SupplierPlanBadges({
  plan,
  verified,
  featured,
  searchBoost,
  className = '',
  compact = false,
}) {
  const p = (plan || 'free').toString().toLowerCase();
  const planLabel = p === 'pro' ? 'PRO Supplier' : p === 'go' ? 'GO Supplier' : 'Free Supplier';
  const planVar = p === 'pro' ? 'primary' : p === 'go' ? 'default' : 'outline';

  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
      {featured && (
        <Badge variant="primary" className="gap-1 text-[10px] sm:text-xs font-bold bg-amber-500/90 text-white border-0">
          <Sparkles className="h-3 w-3" />
          {compact ? 'Featured' : 'Featured supplier'}
        </Badge>
      )}
      <Badge
        variant={planVar}
        className={
          p === 'pro'
            ? 'text-[10px] sm:text-xs font-bold border-violet-300 bg-violet-50 text-violet-800'
            : p === 'go'
              ? 'text-[10px] sm:text-xs font-semibold border-sky-300 bg-sky-50 text-sky-800'
              : 'text-[10px] sm:text-xs'
        }
      >
        {planLabel}
      </Badge>
      {searchBoost && !compact && p === 'pro' && (
        <Badge variant="outline" className="text-[9px] border-teal-200 text-teal-800">
          {searchBoost}
        </Badge>
      )}
      {verified && (
        <Badge variant="success" className="text-[10px] sm:text-xs">
          Verified
        </Badge>
      )}
    </div>
  );
}

export const PAYMENT_STATUS_LABELS = {
  payment_pending: 'Payment pending',
  initiated: 'Payment initiated',
  payment_failed: 'Payment failed',
  processing: 'Processing',
  escrow_held: 'Held in escrow',
  released: 'Released',
  refunded: 'Refunded',
};

export function paymentStatusLabel(code) {
  if (!code) return PAYMENT_STATUS_LABELS.payment_pending;
  return PAYMENT_STATUS_LABELS[code] || String(code).replace(/_/g, ' ');
}
