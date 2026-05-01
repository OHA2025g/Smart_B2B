import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CreditCard, Building2, Smartphone, CheckCircle, XCircle } from 'lucide-react';
import { subscriptionApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';

const METHODS = [
  { id: 'demo_card', label: 'Demo Card', icon: CreditCard },
  { id: 'demo_upi', label: 'Demo UPI', icon: Smartphone },
  { id: 'demo_netbanking', label: 'Demo Net Banking', icon: Building2 },
];

export default function SubscriptionCheckout() {
  const { paymentId } = useParams();
  const navigate = useNavigate();
  const { state: navState } = useLocation();
  const { user } = useAuth();
  const toast = useToast();
  const [me, setMe] = useState(null);
  const [method, setMethod] = useState('demo_card');
  const [outcome, setOutcome] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user?.role !== 'seller') return;
    subscriptionApi
      .getMe()
      .then((r) => setMe(r.data.data))
      .catch(() => setMe(null));
  }, [user?.role]);

  const fromNav = navState?.payment;
  const paymentFromMe = fromNav
    ? fromNav
    : me?.subscription && (me?.subscription?.paymentId === paymentId || String(me?.subscription?.paymentId) === paymentId)
      ? { amount: me.subscription.amount, currency: 'INR' }
      : me?.payment
        ? me.payment
        : null;

  const sim = async (result) => {
    setSubmitting(true);
    try {
      const { data } = await subscriptionApi.simulate(paymentId, { result, method });
      setOutcome(data.data?.ok ? 'success' : 'failed');
      if (data.data?.ok) {
        toast.add('Plan activated (demo).', 'success');
        setTimeout(() => navigate('/seller/subscription'), 1600);
      } else {
        toast.add('Payment failed (demo).', 'error');
      }
    } catch (e) {
      toast.add(e.response?.data?.message || 'Simulation failed', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (user?.role !== 'seller') {
    return (
      <p className="text-center py-12 text-slate-600">
        <Link to="/" className="text-teal-600 font-semibold">
          Home
        </Link>
      </p>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="max-w-lg mx-auto space-y-6">
      <Card>
        <CardHeader>
          <h1 className="text-xl font-bold">Demo Payment Gateway</h1>
          <p className="text-sm text-slate-500 mt-1">
            This is a simulated payment flow for demonstration. No real money is processed.
          </p>
        </CardHeader>
        <CardBody>
          {outcome === 'success' && (
            <div className="flex items-center gap-2 text-emerald-700 font-semibold mb-4">
              <CheckCircle className="h-5 w-5" /> Success — redirecting to your subscription page…
            </div>
          )}
          {outcome === 'failed' && (
            <div className="flex items-center gap-2 text-rose-700 font-semibold mb-4">
              <XCircle className="h-5 w-5" /> Payment failed. You can retry with another simulation.
            </div>
          )}
          <p className="text-sm text-slate-600 font-mono break-all">Payment id: {paymentId}</p>
          {navState?.plan && (
            <p className="text-slate-800 font-semibold mt-2 capitalize">Plan: {String(navState.plan)}</p>
          )}
          {paymentFromMe && (
            <p className="text-slate-800 font-semibold mt-1">Amount: ₹{Number(paymentFromMe.amount || 0).toLocaleString('en-IN')}</p>
          )}

          <p className="text-xs text-slate-500 mt-4">Payment method (demo only)</p>
          <div className="grid gap-2 mt-2">
            {METHODS.map((m) => {
              const Icon = m.icon;
              const active = method === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setMethod(m.id)}
                  className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-left text-sm ${
                    active ? 'border-teal-500 bg-teal-50' : 'border-slate-200'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {m.label}
                </button>
              );
            })}
          </div>
          <div className="flex flex-wrap gap-2 mt-6">
            <Button
              className="flex-1"
              onClick={() => sim('success')}
              disabled={submitting || outcome === 'success'}
            >
              Simulate success
            </Button>
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => sim('failed')}
              disabled={submitting}
            >
              Simulate failure
            </Button>
          </div>
          <Link
            to="/seller/subscription"
            className="text-sm text-teal-600 font-medium mt-4 inline-block"
          >
            Back to plans
          </Link>
        </CardBody>
      </Card>
    </motion.div>
  );
}
