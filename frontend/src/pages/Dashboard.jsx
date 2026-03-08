import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Package, MessageSquare, TrendingUp, Users, Activity, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { inquiriesApi, adminApi, rfqApi, cartApi, wishlistApi, ordersApi } from '../api/client';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';

export default function Dashboard() {
  const { user } = useAuth();
  const [inquiries, setInquiries] = useState([]);
  const [adminSummary, setAdminSummary] = useState(null);
  const [adminDashboard, setAdminDashboard] = useState(null);
  const [buyerStats, setBuyerStats] = useState({ rfqs: 0, cartItems: 0, wishlistItems: 0 });
  const [sellerStats, setSellerStats] = useState({ rfqs: 0, orders: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        if (user?.role === 'admin') {
          const [summaryRes, dashboardRes] = await Promise.all([
            adminApi.summary().catch(() => ({ data: { data: { summary: null } } })),
            adminApi.dashboard().catch(() => ({ data: { data: { dashboard: null } } })),
          ]);
          setAdminSummary(summaryRes.data?.data?.summary ?? null);
          setAdminDashboard(dashboardRes.data?.data?.dashboard ?? null);
        } else if (user?.role === 'buyer') {
          const [inqRes, rfqRes, cartRes, wishRes] = await Promise.all([
            inquiriesApi.getMe().then((r) => r.data.data.inquiries || []).catch(() => []),
            rfqApi.getMy().then((r) => r.data.data.rfqs || []).catch(() => []),
            cartApi.get().then((r) => r.data.data.items || []).catch(() => []),
            wishlistApi.get().then((r) => r.data.data.items || []).catch(() => []),
          ]);
          setInquiries(inqRes);
          setBuyerStats({ rfqs: rfqRes.length, cartItems: cartRes.length, wishlistItems: wishRes.length });
        } else if (user?.role === 'seller') {
          const [inqRes, rfqRes, ordersRes] = await Promise.all([
            inquiriesApi.getMe().then((r) => r.data.data.inquiries || []).catch(() => []),
            rfqApi.getAssigned().then((r) => r.data.data.rfqs || []).catch(() => []),
            ordersApi.getMy().then((r) => r.data.data.orders || []).catch(() => []),
          ]);
          setInquiries(inqRes);
          setSellerStats({ rfqs: rfqRes.length, orders: ordersRes.length });
        } else {
          const { data } = await inquiriesApi.getMe();
          setInquiries(data.data.inquiries || []);
        }
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user?.role]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-neutral-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-neutral-200 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-xl">{error}</div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative rounded-2xl bg-slate-900 text-white p-6 sm:p-8 mb-8 shadow-xl overflow-hidden"
      >
        <div className="absolute inset-0 bg-mesh-dark bg-mesh opacity-60" />
        <div className="relative flex items-center gap-4">
          <div className="h-14 w-14 rounded-xl bg-teal-500/30 flex items-center justify-center">
            <Package className="h-8 w-8 text-teal-200" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Hello, {user?.name}</h1>
            <p className="text-slate-400 text-sm mt-0.5">Here’s what’s happening on your dashboard.</p>
          </div>
        </div>
      </motion.div>

      {user?.role === 'admin' && (adminSummary || adminDashboard) && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <StatCard title="Users" value={adminDashboard?.totalUsers ?? adminSummary?.users ?? 0} icon={Users} />
            <StatCard title="Products" value={adminSummary?.products ?? 0} icon={Package} />
            <StatCard title="Inquiries" value={adminSummary?.inquiries ?? 0} icon={MessageSquare} />
            {adminDashboard && (
              <>
                <StatCard title="Verified suppliers" value={adminDashboard.verifiedSuppliers} icon={Users} />
                <StatCard title="RFQs" value={adminDashboard.totalRfqs} icon={Activity} />
                <StatCard title="Orders" value={adminDashboard.totalOrders} icon={Package} />
              </>
            )}
          </div>
          <Card className="mb-8">
            <CardHeader className="flex flex-row items-center justify-between">
              <span className="font-medium">Recent activity</span>
              <Badge variant="default">Placeholder</Badge>
            </CardHeader>
            <CardBody>
              <ul className="space-y-2 text-sm text-neutral-500">
                <li>Activity feed can be wired to API in a future phase.</li>
              </ul>
            </CardBody>
          </Card>
        </>
      )}

      {(user?.role === 'buyer' || user?.role === 'seller') && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard title="Total inquiries" value={inquiries.length} icon={MessageSquare} />
            <StatCard title="Pending" value={inquiries.filter((i) => i.status === 'pending').length} icon={Activity} />
            {user?.role === 'buyer' && (
              <>
                <StatCard title="My RFQs" value={buyerStats.rfqs} icon={Activity} />
                <StatCard title="Cart items" value={buyerStats.cartItems} icon={Package} />
                <StatCard title="Wishlist" value={buyerStats.wishlistItems} icon={Package} />
              </>
            )}
            {user?.role === 'seller' && (
              <>
                <StatCard title="Assigned RFQs" value={sellerStats.rfqs} icon={TrendingUp} />
                <StatCard title="My orders" value={sellerStats.orders} icon={Package} />
              </>
            )}
          </div>
          <Card>
            <CardHeader>
              <h2 className="font-medium">
                {user?.role === 'buyer' ? 'My Inquiries' : 'Inquiries on my products'}
              </h2>
            </CardHeader>
            <CardBody>
              {inquiries.length === 0 ? (
                <EmptyState
                  icon={MessageSquare}
                  title="No inquiries yet"
                  description={user?.role === 'buyer' ? 'When you send inquiries, they will appear here.' : 'Inquiries from buyers will appear here.'}
                />
              ) : (
                <div className="space-y-4">
                  {inquiries.map((inq, i) => (
                    <motion.div
                      key={inq._id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg border border-neutral-100 hover:bg-neutral-50"
                    >
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-neutral-900">{inq.product?.title}</span>
                          <Badge variant={inq.status === 'pending' ? 'warning' : 'success'}>{inq.status}</Badge>
                          <span className="text-neutral-500 text-sm">Qty: {inq.quantity}</span>
                        </div>
                        <p className="text-sm text-neutral-600 mt-1">{inq.message}</p>
                        {user?.role === 'buyer' && inq.seller && (
                          <p className="text-xs text-neutral-400 mt-1">Seller: {inq.seller.name}</p>
                        )}
                        {user?.role === 'seller' && inq.buyer && (
                          <p className="text-xs text-neutral-400 mt-1">
                            From: {inq.buyer.name} ({inq.buyer?.email})
                          </p>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
          <div className="flex flex-wrap gap-4 mt-6">
            {user?.role === 'buyer' && (
              <>
                <Link to="/cart" className="inline-flex items-center gap-2 text-primary-600 font-medium hover:underline">
                  <ArrowRight className="h-4 w-4" /> RFQ Cart
                </Link>
                <Link to="/wishlist" className="inline-flex items-center gap-2 text-primary-600 font-medium hover:underline">
                  <ArrowRight className="h-4 w-4" /> Wishlist
                </Link>
                <Link to="/rfq" className="inline-flex items-center gap-2 text-primary-600 font-medium hover:underline">
                  <ArrowRight className="h-4 w-4" /> My RFQs
                </Link>
              </>
            )}
            {user?.role === 'seller' && (
              <>
                <Link to="/seller/products" className="inline-flex items-center gap-2 text-primary-600 font-medium hover:underline">
                  <ArrowRight className="h-4 w-4" /> Manage my products
                </Link>
                <Link to="/seller/rfqs" className="inline-flex items-center gap-2 text-primary-600 font-medium hover:underline">
                  <ArrowRight className="h-4 w-4" /> Assigned RFQs
                </Link>
                <Link to="/seller/orders" className="inline-flex items-center gap-2 text-primary-600 font-medium hover:underline">
                  <ArrowRight className="h-4 w-4" /> My orders
                </Link>
              </>
            )}
          </div>
        </>
      )}
    </motion.div>
  );
}
