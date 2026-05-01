import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Check, CreditCard, Sparkles } from 'lucide-react';
import { subscriptionApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { Badge } from '../components/ui/Badge';

const DEMO = 'This is a simulated payment flow for demonstration. No real money is processed.';

export default function Subscription() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [plans, setPlans] = useState([]);
  const [current, setCurrent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');

  useEffect(() => {
    let c = true;
    Promise.all([
      subscriptionApi.getPlans().then((r) => r.data.data?.plans || []),
      subscriptionApi.getMe().then((r) => r.data.data).catch(() => null),
    ])
      .then(([p, m]) => {
        if (c) {
          setPlans(p);
          setCurrent(m);
        }
      })
      .catch(() => {
        if (c) {
          setPlans([]);
        }
      })
      .finally(() => {
        if (c) setLoading(false);
      });
    return () => {
      c = false;
    };
  }, []);

  if (user?.role !== 'seller') {
    return (
      <div className="max-w-lg mx-auto py-16 text-center">
        <p className="text-slate-600">Subscription plans are available to seller accounts.</p>
        <Link to="/dashboard" className="text-teal-600 font-semibold mt-4 inline-block">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const myPlan = (current?.currentPlan?.id || 'free').toLowerCase();
  const isActive = (code) => myPlan === code;

  const handleUpgrade = async (plan) => {
    if (plan === 'free' || isActive(plan)) return;
    setBusy(plan);
    try {
      const { data } = await subscriptionApi.checkout({ plan });
      const path = data.data?.checkoutPath;
      if (path) {
        navigate(path, {
          state: {
            payment: data.data?.payment,
            plan,
          },
        });
      } else {
        toast.add('No checkout path returned', 'error');
      }
    } catch (e) {
      toast.add(e.response?.data?.message || 'Checkout failed', 'error');
    } finally {
      setBusy('');
    }
  };

  if (loading) {
    return <div className="h-40 bg-slate-100 rounded-2xl animate-pulse" />;
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-6xl space-y-8">
      <div>
        <p className="text-xs font-semibold uppercase text-teal-600 tracking-wider">Seller</p>
        <h1 className="page-heading">Subscription &amp; plans</h1>
        <p className="text-slate-500 text-sm mt-1 max-w-2xl">
          {DEMO} SmartB2B &mdash; <strong>Demo Payment Gateway</strong> only.
        </p>
      </div>

      <Card className="border-teal-100 bg-teal-50/50">
        <CardHeader>
          <h2 className="text-lg font-bold text-slate-900">Current plan</h2>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {current?.currentPlan?.name || (myPlan === 'pro' ? 'PRO' : myPlan === 'go' ? 'GO' : 'Free')}
              </p>
              {current?.subscription?.status && (
                <Badge className="mt-2" variant="outline">
                  {current.subscription.status}
                </Badge>
              )}
            </div>
            {isActive('free') && (
              <p className="text-sm text-slate-600">Upgrade to unlock more RFQ visibility and supplier tools.</p>
            )}
          </div>
        </CardBody>
      </Card>

      <div className="grid md:grid-cols-3 gap-6">
        {plans.map((p) => {
          const id = p.id || p.name?.toLowerCase();
          const isCur = (id || '').toLowerCase() === myPlan;
          const isPaid = (id || '') !== 'free';
          return (
            <Card
              key={p.id || p.name}
              className={`overflow-hidden border-2 ${id === 'pro' ? 'border-violet-300 ring-1 ring-violet-200' : 'border-slate-200'}`}
            >
              {id === 'pro' && (
                <div className="text-center text-xs font-bold text-white py-1.5 bg-gradient-to-r from-violet-600 to-indigo-600 flex items-center justify-center gap-1">
                  <Sparkles className="h-3.5 w-3.5" />
                  PRO Supplier visibility
                </div>
              )}
              <div className="p-6 space-y-4">
                <div>
                  <h3 className="text-xl font-bold text-slate-900">{p.name || id}</h3>
                  <p className="text-3xl font-extrabold text-teal-700 mt-2">
                    {p.price_inr != null && p.price_inr > 0 ? `₹${p.price_inr.toLocaleString('en-IN')}` : '₹0'}
                    <span className="text-sm font-medium text-slate-500">/mo</span>
                  </p>
                </div>
                <ul className="text-sm text-slate-600 space-y-2">
                  {(p.features || []).map((f) => (
                    <li key={f} className="flex gap-2">
                      <Check className="h-4 w-4 text-teal-600 shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <div>
                  {isCur ? (
                    <Button variant="secondary" className="w-full" disabled>
                      Current plan
                    </Button>
                  ) : isPaid ? (
                    <Button
                      className="w-full"
                      onClick={() => handleUpgrade((id || '').toLowerCase())}
                      disabled={!!busy}
                    >
                      <CreditCard className="h-4 w-4 mr-2" />
                      {busy === (id || '').toLowerCase() ? 'Starting…' : `Upgrade to ${(p.name || id).toString().toUpperCase()}`}
                    </Button>
                  ) : null}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
