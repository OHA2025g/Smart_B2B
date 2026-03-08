import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ordersApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Package } from 'lucide-react';

export default function SellerOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(null);
  const toast = useToast();

  useEffect(() => {
    ordersApi.getMy()
      .then((res) => setOrders(res.data.data.orders || []))
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, []);

  const handleStatus = async (orderId, status) => {
    setUpdating(orderId);
    try {
      await ordersApi.updateStatus(orderId, status);
      setOrders((prev) => prev.map((o) => (o._id === orderId ? { ...o, status } : o)));
      toast.add('Order updated', 'success');
    } catch {
      toast.add('Update failed', 'error');
    } finally {
      setUpdating(null);
    }
  };

  if (loading) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;
  if (!orders.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">My Orders</h1>
        <Card>
          <EmptyState icon={Package} title="No orders yet" description="Orders will appear here when buyers accept your quotes." />
        </Card>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-2xl font-bold mb-6">My Orders</h1>
      <div className="space-y-4">
        {orders.map((order) => (
          <Card key={order._id}>
            <div className="p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <span className="font-medium">Order #{order._id.slice(-6)}</span>
                <Badge variant={order.status === 'delivered' ? 'success' : order.status === 'cancelled' ? 'danger' : 'primary'}>{order.status}</Badge>
              </div>
              <p className="text-sm text-neutral-500">Buyer: {order.buyerId?.name} · ₹{order.totalAmount}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {order.status === 'created' && (
                  <Button size="sm" onClick={() => handleStatus(order._id, 'confirmed')} disabled={!!updating}>Confirm</Button>
                )}
                {order.status === 'confirmed' && (
                  <>
                    <Button size="sm" onClick={() => handleStatus(order._id, 'processing')} disabled={!!updating}>Processing</Button>
                    <Button size="sm" onClick={() => handleStatus(order._id, 'shipped')} disabled={!!updating}>Mark Shipped</Button>
                  </>
                )}
                {order.status === 'processing' && (
                  <Button size="sm" onClick={() => handleStatus(order._id, 'shipped')} disabled={!!updating}>Mark Shipped</Button>
                )}
                {order.status === 'shipped' && (
                  <Button size="sm" onClick={() => handleStatus(order._id, 'delivered')} disabled={!!updating}>Mark Delivered</Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}
