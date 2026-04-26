import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Package, Clock, Shield, Check, Truck, Box, Sparkles, Printer } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ordersApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { formatDateTimeIst } from '../lib/istTime';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

const LIFECYCLE = [
  { id: 'created', label: 'Created', icon: Package },
  { id: 'confirmed', label: 'Confirmed', icon: Check },
  { id: 'processing', label: 'Processing', icon: Box },
  { id: 'shipped', label: 'Shipped', icon: Truck },
  { id: 'delivered', label: 'Delivered', icon: Sparkles },
];

function stepIndex(status) {
  if (status === 'cancelled') return -1;
  const i = LIFECYCLE.findIndex((s) => s.id === status);
  return i >= 0 ? i : 0;
}



function buildDerivedOrderTimeline(order) {
  if (!order?.createdAt) return [];
  if (order.status === 'cancelled') {
    return [
      {
        _id: 'drv-cancel',
        event_label: 'Order cancelled',
        created_at: order.createdAt,
        actor_role: 'system',
      },
    ];
  }
  const seq = [
    { st: 'created', label: 'Order placed', role: 'buyer' },
    { st: 'confirmed', label: 'Order confirmed', role: 'seller' },
    { st: 'processing', label: 'Order processing', role: 'seller' },
    { st: 'shipped', label: 'Order shipped', role: 'seller' },
    { st: 'delivered', label: 'Order delivered', role: 'seller' },
  ];
  const ix = seq.findIndex((s) => s.st === order.status);
  const n = ix >= 0 ? ix + 1 : 1;
  const ts = order.createdAt;
  return seq.slice(0, n).map((s) => ({
    _id: `drv-${s.st}`,
    event_label: s.label,
    created_at: ts,
    actor_role: s.role,
  }));
}


export default function OrderDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [order, setOrder] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [paymentUpdating, setPaymentUpdating] = useState(false);
  const toast = useToast();

  useEffect(() => {
    ordersApi
      .getById(id)
      .then((r) => setOrder(r.data.data.order))
      .catch(() => setOrder(null))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!order) return;
    ordersApi
      .getTimeline(id)
      .then((r) => setTimeline(r.data.data.timeline || []))
      .catch(() => setTimeline([]));
  }, [order, id]);

  const displayTimeline = useMemo(() => {
    if (!order) return [];
    if (timeline.length) return timeline;
    return buildDerivedOrderTimeline(order);
  }, [order, timeline]);

  const handleStatus = async (status) => {
    setUpdating(true);
    try {
      await ordersApi.updateStatus(id, status);
      const { data } = await ordersApi.getById(id);
      setOrder(data.data.order);
      const tr = await ordersApi.getTimeline(id);
      setTimeline(tr.data.data.timeline || []);
      toast.add('Order updated', 'success');
    } catch {
      toast.add('Update failed', 'error');
    } finally {
      setUpdating(false);
    }
  };

  const handlePayment = async (paymentStatus) => {
    setPaymentUpdating(true);
    try {
      await ordersApi.updatePayment(id, paymentStatus);
      const { data } = await ordersApi.getById(id);
      setOrder(data.data.order);
      const tr = await ordersApi.getTimeline(id);
      setTimeline(tr.data.data.timeline || []);
      toast.add('Payment status updated', 'success');
    } catch {
      toast.add('Update failed', 'error');
    } finally {
      setPaymentUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl space-y-4">
        <div className="h-10 w-56 bg-slate-200 rounded-xl animate-pulse" />
        <div className="h-40 bg-slate-100 rounded-2xl animate-pulse" />
      </div>
    );
  }
  if (!order) {
    return (
      <div className="text-center py-16 max-w-md mx-auto">
        <p className="text-slate-600 mb-6">Order not found.</p>
        <Link to="/orders" className="text-teal-600 font-semibold hover:underline">
          Back to orders
        </Link>
      </div>
    );
  }

  const sellerId = order.sellerId?.id || order.sellerId?._id || order.sellerId;
  const isSeller = user && String(sellerId) === String(user.id || user._id);
  const idx = stepIndex(order.status);
  const oid = String(order._id || order.id || '');
  const poNo = `PO-${oid.slice(-8).toUpperCase()}`;
  const invNo = `INV-${oid.slice(-8).toUpperCase()}`;
  const buyerCo = order.buyerCompany || order.buyerId?.name || '—';
  const sellerCo = order.sellerCompany || order.sellerId?.name || '—';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4 print:hidden">
        <div>
          <p className="section-heading mb-1">Order</p>
          <h1 className="page-heading">#{oid.slice(-6)}</h1>
          <p className="text-sm text-slate-500 mt-1">Fulfillment progress and commercial summary.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="rounded-xl gap-2 print:hidden"
            onClick={() => window.print()}
          >
            <Printer className="h-4 w-4" /> Print / Download
          </Button>
          <Badge
            variant={order.status === 'delivered' ? 'success' : order.status === 'cancelled' ? 'danger' : 'primary'}
            className="font-semibold px-3 py-1 capitalize text-sm"
          >
            {order.status}
          </Badge>
        </div>
      </div>

      <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40 print:hidden">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="section-title">Order summary</h2>
        </div>
        <div className="p-5 sm:p-6 grid sm:grid-cols-2 gap-6">
          <div className="space-y-3 text-sm">
            <div>
              <p className="section-heading mb-1">Buyer</p>
              <p className="font-semibold text-slate-900">{buyerCo}</p>
            </div>
            <div>
              <p className="section-heading mb-1">Seller</p>
              <p className="font-semibold text-slate-900">{sellerCo}</p>
            </div>
            <div>
              <p className="section-heading mb-1">Placed</p>
              <p className="text-slate-700">{order.createdAt ? formatDateTimeIst(order.createdAt) : '—'}</p>
            </div>
          </div>
          <div className="rounded-2xl bg-gradient-to-br from-teal-50 to-slate-50 border border-teal-100/80 p-6 flex flex-col justify-center">
            <p className="text-xs font-semibold uppercase tracking-wide text-teal-800/80">Total</p>
            <p className="text-3xl font-bold text-teal-700 tabular-nums mt-1">₹{order.totalAmount}</p>
            <p className="text-xs text-slate-500 mt-2">Includes agreed line totals from accepted quote.</p>
          </div>
        </div>
      </Card>

      <Card className="border-slate-200/90 overflow-hidden print:hidden">
        <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
          <h2 className="section-title flex items-center gap-2">
            <Package className="h-5 w-5 text-teal-600" /> Tracking
          </h2>
          <p className="text-sm text-slate-500 mt-1">Created → Confirmed → Processing → Shipped → Delivered</p>
        </div>
        <div className="p-5 sm:p-8">
          {order.status === 'cancelled' ? (
            <p className="text-sm text-rose-600 font-medium">This order was cancelled.</p>
          ) : (
            <div>
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-6 sm:gap-2">
                {LIFECYCLE.map((s, i) => {
                  const done = i <= idx;
                  const active = i === idx && order.status !== 'cancelled';
                  const Icon = s.icon;
                  return (
                    <div key={s.id} className="flex sm:flex-col items-center sm:text-center gap-4 sm:gap-3 relative z-10">
                      <div
                        className={`flex h-14 w-14 shrink-0 rounded-2xl items-center justify-center transition-all ${
                          done
                            ? 'bg-teal-600 text-white shadow-lg shadow-teal-600/35'
                            : 'bg-slate-100 text-slate-400 ring-2 ring-slate-200'
                        }${active ? ' ring-4 ring-amber-300 ring-offset-2' : ''}`}
                      >
                        <Icon className="h-6 w-6" />
                      </div>
                      <div>
                        <p className={`font-bold text-sm ${done ? 'text-slate-900' : 'text-slate-400'}`}>{s.label}</p>
                        <p className="text-xs text-slate-500 mt-0.5 capitalize">{s.id}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {isSeller && order.status !== 'cancelled' && order.status !== 'delivered' && (
            <div className="mt-8 pt-6 border-t border-slate-100 flex flex-wrap gap-2">
              {order.status === 'created' && (
                <Button size="sm" disabled={updating} onClick={() => handleStatus('confirmed')} className="rounded-xl">
                  Confirm order
                </Button>
              )}
              {order.status === 'confirmed' && (
                <>
                  <Button size="sm" disabled={updating} onClick={() => handleStatus('processing')} className="rounded-xl">
                    Start processing
                  </Button>
                  <Button size="sm" variant="secondary" disabled={updating} onClick={() => handleStatus('shipped')} className="rounded-xl">
                    Mark shipped
                  </Button>
                </>
              )}
              {order.status === 'processing' && (
                <Button size="sm" disabled={updating} onClick={() => handleStatus('shipped')} className="rounded-xl">
                  Mark shipped
                </Button>
              )}
              {order.status === 'shipped' && (
                <Button size="sm" disabled={updating} onClick={() => handleStatus('delivered')} className="rounded-xl">
                  Mark delivered
                </Button>
              )}
            </div>
          )}
        </div>
      </Card>

      <Card className="border-slate-200/90 print:hidden">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="section-title">Line items</h2>
        </div>
        <ul className="divide-y divide-slate-100">
          {(order.items || []).map((it, i) => (
            <li key={i} className="px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <p className="font-semibold text-slate-900">{it.productId?.title || 'Product'}</p>
                <p className="text-xs text-slate-500 mt-1">Agreed unit economics</p>
              </div>
              <div className="text-left sm:text-right">
                <p className="text-sm font-semibold text-slate-800 tabular-nums">
                  {it.quantity} × ₹{it.agreedUnitPrice}
                </p>
                <p className="text-xs text-teal-700 font-medium tabular-nums mt-0.5">
                  Subtotal ₹{(Number(it.quantity) || 0) * (Number(it.agreedUnitPrice) || 0)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      <Card id="smartb2b-po-invoice" className="print-invoice-root border-slate-300 border-2 overflow-hidden bg-white">
        <div className="px-6 py-5 border-b border-slate-200 flex flex-wrap items-start justify-between gap-4 bg-slate-50">
          <div>
            <p className="text-2xl font-bold text-teal-700 tracking-tight">B2Bभारत</p>
            <p className="text-xs text-slate-500 mt-1">B2B marketplace · Purchase order &amp; tax invoice (demo)</p>
          </div>
          <div className="text-right text-sm">
            <p className="font-mono font-bold text-slate-900">{poNo}</p>
            <p className="font-mono text-slate-600">{invNo}</p>
          </div>
        </div>
        <div className="p-6 grid sm:grid-cols-2 gap-6 text-sm">
          <div>
            <p className="section-heading mb-2">Bill to (buyer)</p>
            <p className="font-bold text-slate-900">{buyerCo}</p>
            {order.buyerId?.email && <p className="text-slate-600 mt-1">{order.buyerId.email}</p>}
          </div>
          <div>
            <p className="section-heading mb-2">Supplier (seller)</p>
            <p className="font-bold text-slate-900">{sellerCo}</p>
            {order.sellerId?.email && <p className="text-slate-600 mt-1">{order.sellerId.email}</p>}
          </div>
          <div>
            <p className="section-heading mb-1">Order date</p>
            <p className="font-medium text-slate-800">{order.createdAt ? formatDateTimeIst(order.createdAt) : '—'}</p>
          </div>
          <div>
            <p className="section-heading mb-1">Status</p>
            <p className="font-semibold capitalize text-slate-900">{order.status}</p>
          </div>
          <div>
            <p className="section-heading mb-1">RFQ reference</p>
            <p className="font-mono text-xs text-slate-700 break-all">{order.rfqId ? String(order.rfqId) : '—'}</p>
          </div>
          <div>
            <p className="section-heading mb-1">Quote reference</p>
            <p className="font-mono text-xs text-slate-700 break-all">{order.quoteId ? String(order.quoteId) : '—'}</p>
          </div>
        </div>
        <div className="px-6 pb-6">
          <p className="section-heading mb-2">Items</p>
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-100 text-left text-xs uppercase tracking-wide text-slate-600">
                  <th className="py-3 px-4 font-semibold">Product</th>
                  <th className="py-3 px-4 font-semibold">Qty</th>
                  <th className="py-3 px-4 font-semibold">Unit price</th>
                  <th className="py-3 px-4 font-semibold text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {(order.items || []).map((it, i) => {
                  const sub = (Number(it.quantity) || 0) * (Number(it.agreedUnitPrice) || 0);
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="py-3 px-4 font-medium text-slate-900">{it.productId?.title || 'Product'}</td>
                      <td className="py-3 px-4 tabular-nums">{it.quantity}</td>
                      <td className="py-3 px-4 tabular-nums">₹{it.agreedUnitPrice}</td>
                      <td className="py-3 px-4 text-right font-semibold tabular-nums">₹{sub}</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-teal-50/80 border-t border-teal-100">
                  <td colSpan={3} className="py-3 px-4 text-right font-bold text-slate-800">
                    Total
                  </td>
                  <td className="py-3 px-4 text-right font-bold text-teal-800 tabular-nums">₹{order.totalAmount}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50/80 p-4 text-sm text-slate-700">
            <p className="font-semibold text-slate-900 mb-1">Payment &amp; escrow</p>
            <p className="text-xs leading-relaxed">
              On-platform escrow and milestone releases are not active in this demo build. Settlement terms follow your
              negotiated quote and offline arrangements.
            </p>
          </div>
          <p className="mt-4 text-xs text-slate-500">
            Terms: Goods as per agreed specifications. B2Bभारत provides a record of the order only.
          </p>
        </div>
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 print:hidden">
          <Button type="button" variant="secondary" size="sm" className="rounded-xl gap-2" onClick={() => window.print()}>
            <Printer className="h-4 w-4" /> Print / Download
          </Button>
        </div>
      </Card>

      <Card className="print:hidden border-slate-200/90">
        <div className="px-5 py-4 border-b border-slate-100">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="section-title flex items-center gap-2">
              <Shield className="h-5 w-5 text-teal-600" />
              Escrow payment protection
            </h2>
            <Badge variant="primary">{(order.paymentStatus || 'payment_pending').replace(/_/g, ' ')}</Badge>
          </div>
          <p className="text-xs text-slate-500 mt-2 max-w-3xl">
            Communication is monitored to maintain buyer-seller trust. No real payment provider is connected—use the demo
            actions to walk through a typical release workflow.
          </p>
        </div>
        <ol className="p-5 sm:p-6 space-y-2 text-sm text-slate-700 list-decimal list-inside">
          <li>Buyer initiates payment</li>
          <li>B2Bभारत holds amount securely (escrow)</li>
          <li>Seller ships goods (order status)</li>
          <li>Buyer confirms delivery</li>
          <li>Payment released to seller (or refunded if applicable)</li>
        </ol>
        <div className="px-5 pb-5 flex flex-wrap gap-2 print:hidden">
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('payment_pending')}
            variant="secondary"
          >
            1. Mark payment initiated
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('escrow_held')}
            variant="secondary"
          >
            2. Mark escrow held
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('released')}
            variant="primary"
          >
            3. Mark released
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('refunded')}
            variant="ghost"
            className="text-amber-700"
          >
            Mark refunded
          </Button>
        </div>
      </Card>



      {displayTimeline.length > 0 && (
        <Card className="border-slate-200/90 print:hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <Clock className="h-5 w-5 text-teal-600" />
            <h2 className="section-title">Timeline</h2>
            {!timeline.length && (
              <Badge variant="outline" className="text-[10px] ml-2">
                Derived from status
              </Badge>
            )}
          </div>
          <ul className="p-5 sm:p-6 space-y-4">
            {displayTimeline.map((e) => (
              <li key={e._id || e.id} className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 text-sm border-b border-slate-50 last:border-0 pb-4 last:pb-0">
                <span className="text-xs font-medium text-slate-400 tabular-nums shrink-0 sm:w-44">
                  {e.created_at ? formatDateTimeIst(e.created_at) : ''}
                </span>
                <span className="font-semibold text-slate-900 flex-1">{e.event_label}</span>
                <Badge variant="outline" className="w-fit text-[10px]">
                  {e.actor_role}
                </Badge>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </motion.div>
  );
}
