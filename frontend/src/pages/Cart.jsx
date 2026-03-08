import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingCart, Trash2, FileText } from 'lucide-react';
import { cartApi, rfqApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { EmptyState } from '../components/ui/EmptyState';

export default function Cart() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

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
      const { data } = await cartApi.get();
      const cartItems = data.data.items || [];
      if (!cartItems.length) {
        toast.add('Cart is empty', 'error');
        setCreating(false);
        return;
      }
      const { data: res } = await rfqApi.create({ fromCart: true });
      toast.add('RFQ created', 'success');
      navigate(`/rfq/${res.data?.rfq?._id || res.data?.rfq?.id}`);
    } catch (e) {
      toast.add(e.response?.data?.message || 'Failed to create RFQ', 'error');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;
  if (!items.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">RFQ Cart</h1>
        <Card>
          <EmptyState
            icon={ShoppingCart}
            title="Your cart is empty"
            description="Add products from the Products page to request quotations."
            action={<Link to="/products"><Button>Browse products</Button></Link>}
          />
        </Card>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">RFQ Cart</h1>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={handleClear}>Clear cart</Button>
          <Button className="gap-2" onClick={handleCreateRFQ} disabled={creating}>
            <FileText className="h-4 w-4" /> Request Quotation (RFQ)
          </Button>
        </div>
      </div>
      <Card>
        <ul className="divide-y divide-neutral-200">
          {items.map((item) => {
            const p = item.productId;
            if (!p) return null;
            return (
              <li key={item._id} className="p-4 flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex-1">
                  <Link to={`/product/${p._id}`} className="font-medium text-primary-600 hover:underline">{p.title}</Link>
                  <p className="text-sm text-neutral-500">{p.category} · ₹{p.price}/{p.unit}</p>
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
    </motion.div>
  );
}
