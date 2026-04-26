import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingCart, Trash2, FileText, MapPin, Calendar } from 'lucide-react';
import { cartApi, rfqApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';

function defaultDateDays(ahead) {
  const d = new Date();
  d.setDate(d.getDate() + ahead);
  return d.toISOString().slice(0, 10);
}

export default function Cart() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deliveryLocation, setDeliveryLocation] = useState('');
  const [requiredByDate, setRequiredByDate] = useState(() => defaultDateDays(14));
  const [buyerNotes, setBuyerNotes] = useState('');
  const [priority, setPriority] = useState('normal');
  const [validUntil, setValidUntil] = useState('');
  const navigate = useNavigate();
  const toast = useToast();

  const canSubmitRfq = useMemo(
    () => deliveryLocation.trim().length > 0 && Boolean(requiredByDate) && items.length > 0,
    [deliveryLocation, requiredByDate, items.length],
  );

  const fetchCart = async () => {
    try {
      const { data } = await cartApi.get();
      setItems(data.data.items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const handleUpdate = async (productId, quantity, notes) => {
    try {
      await cartApi.add({ productId, quantity: Math.max(1, quantity), notes });
      fetchCart();
      toast.add('Cart updated', 'success');
    } catch {
      toast.add('Update failed', 'error');
    }
  };

  const handleRemove = async (productId) => {
    try {
      await cartApi.remove(productId);
      setItems((prev) => prev.filter((i) => i.productId?._id !== productId));
      toast.add('Removed from cart', 'success');
    } catch {
      toast.add('Failed to remove', 'error');
    }
  };

  const handleClear = async () => {
    try {
      await cartApi.clear();
      setItems([]);
      toast.add('Cart cleared', 'success');
    } catch {
      toast.add('Failed to clear', 'error');
    }
  };

  const handleCreateRFQ = async () => {
    setCreating(true);
    try {
      const { data: cartRes } = await cartApi.get();
      const cartItems = cartRes.data.items || [];
      if (!cartItems.length) {
        toast.add('Cart is empty', 'error');
        setCreating(false);
        return;
      }
      if (!deliveryLocation.trim()) {
        toast.add('Delivery location is required', 'error');
        setCreating(false);
        return;
      }
      if (!requiredByDate) {
        toast.add('Required-by date is required', 'error');
        setCreating(false);
        return;
      }
      const rbd = new Date(`${requiredByDate}T12:00:00.000Z`).toISOString();
      const payload = {
        fromCart: true,
        deliveryLocation: deliveryLocation.trim(),
        requiredByDate: rbd,
        buyerNotes: buyerNotes.trim() || undefined,
        priority,
      };
      if (validUntil?.trim()) {
        payload.validUntil = new Date(`${validUntil.trim()}T12:00:00.000Z`).toISOString();
      }
      const { data: res } = await rfqApi.create(payload);
      toast.add('RFQ created', 'success');
      const rid = res.data?.rfq?._id || res.data?.rfq?.id;
      navigate(rid ? `/rfq/${rid}` : '/rfq');
    } catch (e) {
      const msg = e.response?.data?.message || e.response?.data?.detail;
      if (Array.isArray(msg) && msg[0]?.message) {
        toast.add(String(msg[0].message), 'error');
      } else {
        toast.add(typeof msg === 'string' ? msg : 'Failed to create RFQ', 'error');
      }
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;
  }
  if (!items.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">RFQ Cart</h1>
        <Card>
          <EmptyState
            icon={ShoppingCart}
            title="Your cart is empty"
            description="Add products from the Products page to request quotations."
            action={(
              <Link to="/products">
                <Button>Browse products</Button>
              </Link>
            )}
          />
        </Card>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">RFQ Cart</h1>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={handleClear}>
            Clear cart
          </Button>
        </div>
      </div>

      <Card>
        <p className="text-sm text-slate-500 mb-4">Review line items, then add delivery and scheduling below.</p>
        <ul className="divide-y divide-neutral-200">
          {items.map((item) => {
            const p = item.productId;
            if (!p) return null;
            return (
              <li key={item._id} className="py-4 flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex-1">
                  <Link to={`/product/${p._id}`} className="font-medium text-primary-600 hover:underline">
                    {p.title}
                  </Link>
                  <p className="text-sm text-neutral-500">
                    {p.category} {String.fromCharCode(183)} {p.price}/{p.unit}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <input
                    type="number"
                    min={1}
                    value={item.quantity}
                    onChange={(e) => handleUpdate(p._id, Number(e.target.value), item.notes)}
                    className="w-20 border rounded px-2 py-1 text-center"
                  />
                  <input
                    type="text"
                    placeholder="Notes"
                    value={item.notes || ''}
                    onChange={(e) => handleUpdate(p._id, item.quantity, e.target.value)}
                    className="w-32 border rounded px-2 py-1 text-sm"
                  />
                  <Button variant="ghost" size="sm" className="text-red-600" onClick={() => handleRemove(p._id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      </Card>

      <Card className="p-5 space-y-4">
        <div>
          <h2 className="text-lg font-semibold">RFQ details</h2>
          <p className="text-sm text-slate-500 mt-1">Suppliers and admins will see this with your request.</p>
        </div>
        <div className="space-y-3">
          <div>
            <label className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500 mb-1">
              <MapPin className="h-3.5 w-3.5" />
              Delivery location
            </label>
            <Input
              value={deliveryLocation}
              onChange={(e) => setDeliveryLocation(e.target.value)}
              placeholder="e.g. Warehouse 4, 100 Industrial Way, City"
            />
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500 mb-1">
                <Calendar className="h-3.5 w-3.5" />
                Required by
              </label>
              <Input type="date" value={requiredByDate} onChange={(e) => setRequiredByDate(e.target.value)} />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500 mb-1">RFQ valid until (optional)</label>
              <Input
                type="date"
                value={validUntil}
                onChange={(e) => setValidUntil(e.target.value)}
                placeholder="Defaults to 7 days from today"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500 mb-1">Priority</label>
            <Select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              options={[
                { value: 'normal', label: 'Normal' },
                { value: 'urgent', label: 'Urgent' },
              ]}
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500 mb-1">Buyer notes</label>
            <textarea
              value={buyerNotes}
              onChange={(e) => setBuyerNotes(e.target.value)}
              className="w-full min-h-[100px] rounded-lg border border-slate-200 px-3 py-2 text-sm"
              placeholder="Context, incoterms, or receiving constraints."
            />
          </div>
        </div>
        <div className="pt-2 flex flex-wrap gap-2 justify-end">
          <Button
            className="gap-2"
            onClick={handleCreateRFQ}
            disabled={creating || !canSubmitRfq}
          >
            <FileText className="h-4 w-4" />
            {creating ? 'Creating...' : 'Create RFQ'}
          </Button>
        </div>
        {!canSubmitRfq && (
          <p className="text-xs text-amber-600">Set delivery location and required-by date to create your RFQ.</p>
        )}
      </Card>
    </motion.div>
  );
}

