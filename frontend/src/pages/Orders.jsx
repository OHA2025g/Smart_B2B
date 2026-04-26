import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDateTimeIst } from '../lib/istTime';
import { motion } from 'framer-motion';
import { Package } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ordersApi, adminApi } from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { EmptyState } from '../components/ui/EmptyState';

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'created', label: 'Created' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'processing', label: 'Processing' },
  { value: 'shipped', label: 'Shipped' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'cancelled', label: 'Cancelled' },
];

function badgeVariant(status) {
  if (status === 'delivered') return 'success';
  if (status === 'cancelled') return 'danger';
  return 'primary';
}

export default function Orders() {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const p =
      user?.role === 'admin'
        ? adminApi.getOrders()
        : ordersApi.getMy(status ? { status } : undefined);
    p.then((res) => {
      if (!cancelled) setOrders(res.data.data.orders || []);
    })
      .catch(() => {
        if (!cancelled) setOrders([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user?.role, status]);

  const filtered = useMemo(() => {
    let list = orders;
    if (user?.role === 'admin' && status) {
      list = list.filter((o) => o.status === status);
    }
    const q = search.trim().toLowerCase();
    if (!q) return list;
    return list.filter((o) => {
      const idShort = String(o._id || o.id || '').toLowerCase();
      const buyerCo = (o.buyerCompany || o.buyerId?.name || '').toLowerCase();
      const sellerCo = (o.sellerCompany || o.sellerId?.name || '').toLowerCase();
      return idShort.includes(q) || buyerCo.includes(q) || sellerCo.includes(q);
    });
  }, [orders, search, status, user?.role]);

  const title =
    user?.role === 'admin' ? 'All orders' : user?.role === 'seller' ? 'Orders received' : 'Orders placed';
  const subtitle =
    user?.role === 'admin'
      ? 'Platform-wide order ledger.'
      : user?.role === 'seller'
        ? 'Fulfillment queue from accepted quotes.'
        : 'Orders created when you accept a supplier quote.';

  if (loading) {
    return (
      <div className="max-w-5xl space-y-4">
        <div className="h-10 w-48 bg-slate-200 rounded-xl animate-pulse" />
        <div className="h-32 bg-slate-100 rounded-2xl animate-pulse" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-5xl space-y-6">
      <div>
        <p className="section-heading mb-1">Fulfillment</p>
        <h1 className="page-heading">{title}</h1>
        <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
      </div>

      <Card className="p-4 sm:p-5 border-slate-200/90">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="sm:w-48">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value || 'all'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-0">
            <Input
              label="Search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Order id, buyer or seller company…"
            />
          </div>
        </div>
      </Card>

      {!filtered.length ? (
        <Card>
          <EmptyState
            icon={Package}
            title="No orders match"
            description={orders.length ? 'Try adjusting filters or search.' : 'No orders yet.'}
          />
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((o) => {
            const oid = o._id || o.id;
            const buyerLabel = o.buyerCompany || o.buyerId?.name || 'Buyer';
            const sellerLabel = o.sellerCompany || o.sellerId?.name || 'Seller';
            return (
              <Card key={oid} className="border-slate-200/90 overflow-hidden">
                <div className="p-4 sm:p-5 flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0 space-y-1">
                    <p className="font-mono text-xs text-slate-500">#{String(oid).slice(-8)}</p>
                    <p className="font-semibold text-slate-900">
                      {user?.role === 'seller' ? (
                        <>
                          Buyer: <span className="text-teal-700">{buyerLabel}</span>
                        </>
                      ) : user?.role === 'admin' ? (
                        <>
                          {buyerLabel} <span className="text-slate-400">→</span> {sellerLabel}
                        </>
                      ) : (
                        <>
                          Seller: <span className="text-teal-700">{sellerLabel}</span>
                        </>
                      )}
                    </p>
                    <p className="text-xs text-slate-500">
                      {o.createdAt ? formatDateTimeIst(o.createdAt) : '—'}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <Badge variant={badgeVariant(o.status)} className="capitalize font-semibold">
                      {o.status}
                    </Badge>
                    <p className="text-lg font-bold text-slate-900 tabular-nums">₹{o.totalAmount ?? '—'}</p>
                    <Link
                      to={`/orders/${oid}`}
                      className="inline-flex items-center justify-center font-medium rounded-xl px-3 py-1.5 text-sm bg-teal-600 text-white hover:bg-teal-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
                    >
                      View details
                    </Link>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
