import { useEffect, useState } from 'react';
import { Shield, Wallet, ChevronRight } from 'lucide-react';
import { ordersApi } from '../api/client';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { useToast } from './ui/Toast';
import { paymentStatusLabel } from './SupplierPlanBadges';

const STEPS = [
  'Buyer pays (demo)',
  'Held in SmartB2B escrow',
  'Seller ships (order status)',
  'Mark delivered',
  'Release to seller',
];

const METHODS = [
  { id: 'demo_card', label: 'Demo card' },
  { id: 'demo_upi', label: 'Demo UPI' },
  { id: 'demo_netbanking', label: 'Demo net banking' },
];

export function OrderPaymentPanel({ order, orderId, user, onOrderUpdate }) {
  const toast = useToast();
  const [payments, setPayments] = useState([]);
  const [modal, setModal] = useState(false);
  const [method, setMethod] = useState('demo_card');
  const [busy, setBusy] = useState(false);
  const [activePaymentId, setActivePaymentId] = useState(null);

  const isBuyer = user?.role === 'buyer' && String(order?.buyerId?._id || order?.buyerId?.id || order?.buyerId) === String(user?.id);
  const isAdmin = user?.role === 'admin';

  const pay = order?.paymentStatus || 'payment_pending';
  const escrow = order?.escrowStatus || 'not_started';

  useEffect(() => {
    if (!orderId) return;
    ordersApi
      .getPayments(orderId)
      .then((r) => setPayments(r.data.data?.payments || []))
      .catch(() => setPayments([]));
  }, [orderId, pay]);

  const latest = payments[0];
  const stepIndex =
    pay === 'payment_pending' || pay === 'payment_failed'
      ? 0
      : pay === 'initiated' || pay === 'processing'
        ? 0
        : pay === 'escrow_held'
          ? 1
          : pay === 'released'
            ? 4
            : pay === 'refunded'
              ? 3
              : 0;

  const startPay = async () => {
    setBusy(true);
    try {
      const { data } = await ordersApi.initiatePayment(orderId);
      setActivePaymentId(data.data?.payment?._id || data.data?.payment?.id);
      onOrderUpdate(data.data.order);
      setModal(true);
      toast.add('Demo payment started.', 'success');
    } catch (e) {
      toast.add(e.response?.data?.message || e.response?.data?.detail?.[0] || 'Could not start payment', 'error');
    } finally {
      setBusy(false);
    }
  };

  const sim = async (result) => {
    const pid = activePaymentId || latest?._id || latest?.id;
    if (!pid) {
      toast.add('No payment id. Initiate first.', 'error');
      return;
    }
    const payId = String(pid);
    setBusy(true);
    try {
      const { data } = await ordersApi.simulateOrderPayment(orderId, payId, { result, method });
      onOrderUpdate(data.data.order);
      setPayments((prev) => {
        const next = [data.data.payment, ...prev.filter((x) => (x._id || x.id) !== (data.data.payment?._id || data.data.payment?.id))];
        return next;
      });
      setModal(false);
      toast.add(result === 'success' ? 'Payment held in escrow (demo).' : 'Payment failed (demo).', result === 'success' ? 'success' : 'error');
    } catch (e) {
      toast.add(e.response?.data?.message || 'Simulation failed', 'error');
    } finally {
      setBusy(false);
    }
  };

  const release = async () => {
    setBusy(true);
    try {
      const { data } = await ordersApi.releaseEscrow(orderId);
      onOrderUpdate(data.data.order);
      toast.add('Payment released (demo).', 'success');
    } catch (e) {
      toast.add(e.response?.data?.message || 'Release failed', 'error');
    } finally {
      setBusy(false);
    }
  };

  const canStartNewPayment =
    isBuyer &&
    order?.status !== 'cancelled' &&
    (pay === 'payment_pending' || pay === 'payment_failed');

  const canOpenDemoModal =
    isBuyer &&
    order?.status !== 'cancelled' &&
    (canStartNewPayment || pay === 'initiated' || pay === 'processing');

  const showRelease =
    (isBuyer && order?.status === 'delivered' && (pay === 'escrow_held' || escrow === 'held')) ||
    (isAdmin && (pay === 'escrow_held' || escrow === 'held'));

  return (
    <>
      <Card className="print:hidden border-slate-200/90 border-2 border-dashed border-teal-200/80 bg-gradient-to-b from-slate-50/50 to-white">
        <div className="px-5 py-4 border-b border-slate-100">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="section-title flex items-center gap-2">
              <Wallet className="h-5 w-5 text-teal-600" />
              Demo Payment Gateway
            </h2>
            <Badge variant="primary" className="text-xs">
              {paymentStatusLabel(pay)}
            </Badge>
          </div>
          <p className="text-xs text-amber-800/90 bg-amber-50 border border-amber-100 rounded-lg px-2 py-1.5 mt-2">
            This is a simulated payment flow for demonstration. No real money is processed.
          </p>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase">Escrow timeline</p>
            <ol className="mt-2 space-y-1">
              {STEPS.map((s, i) => (
                <li key={s} className="flex items-center gap-2 text-sm text-slate-700">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                      i <= stepIndex ? 'bg-teal-600 text-white' : 'bg-slate-200 text-slate-500'
                    }`}
                  >
                    {i + 1}
                  </span>
                  {s}
                  {i < STEPS.length - 1 && <ChevronRight className="h-3 w-3 text-slate-300 hidden sm:block" />}
                </li>
              ))}
            </ol>
          </div>
          {canOpenDemoModal && (
            <Button
              type="button"
              className="rounded-xl gap-2"
              onClick={async () => {
                if (canStartNewPayment) await startPay();
                else {
                  setActivePaymentId((latest?._id || latest?.id) ?? activePaymentId);
                  setModal(true);
                }
              }}
              disabled={busy}
            >
              <Shield className="h-4 w-4" />
              {canStartNewPayment ? 'Pay via demo gateway' : 'Open demo payment'}
            </Button>
          )}
          {showRelease && (
            <Button type="button" variant="primary" className="rounded-xl" onClick={release} disabled={busy}>
              Release payment (demo)
            </Button>
          )}
          {isAdmin && (pay === 'escrow_held' || escrow === 'held') && order?.status !== 'delivered' && (
            <p className="text-xs text-slate-500">Admin demo: you can release escrow even if the order is not marked delivered yet.</p>
          )}
        </div>
      </Card>

      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm print:hidden" role="dialog">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 p-6 space-y-4">
            <h3 className="text-lg font-bold">Demo order payment</h3>
            <p className="text-2xl font-extrabold text-teal-700">₹{Number(order?.totalAmount || 0).toLocaleString('en-IN')}</p>
            <div>
              <p className="text-xs font-semibold text-slate-500 mb-2">Method</p>
              <div className="grid gap-2">
                {METHODS.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    className={`text-left rounded-xl border px-3 py-2 text-sm ${
                      method === m.id ? 'border-teal-500 bg-teal-50' : 'border-slate-200'
                    }`}
                    onClick={() => setMethod(m.id)}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <Button className="flex-1" onClick={() => sim('success')} disabled={busy}>
                Simulate success
              </Button>
              <Button variant="secondary" className="flex-1" onClick={() => sim('failed')} disabled={busy}>
                Simulate failure
              </Button>
            </div>
            <Button variant="ghost" className="w-full" onClick={() => setModal(false)}>
              Close
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
