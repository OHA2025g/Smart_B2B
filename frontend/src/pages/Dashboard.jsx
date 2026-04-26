import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from 'recharts';
import { Package, MessageSquare, TrendingUp, Users, Activity, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { inquiriesApi, adminApi, rfqApi, cartApi, wishlistApi, ordersApi, buyerDashboardApi, sellerDashboardApi } from '../api/client';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';

const CHART_COLORS = ['#0d9488', '#f43f5e', '#6366f1', '#f59e0b', '#94a3b8', '#10b981', '#8b5cf6'];

/** Logical order for fulfillment / order-status pies (legend + slices read left-to-right in pipeline). */
const ORDER_STATUS_PIPELINE = ['created', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'];

const RFQ_STATUS_PIPELINE = ['sent', 'quoted', 'accepted', 'closed'];

function distToPieData(dist, pipelineOrder = null) {
  if (!dist || typeof dist !== 'object') return [];
  let entries = Object.entries(dist);
  if (pipelineOrder?.length) {
    entries = [...entries].sort((a, b) => {
      const ia = pipelineOrder.indexOf(a[0]);
      const ib = pipelineOrder.indexOf(b[0]);
      if (ia === -1 && ib === -1) return a[0].localeCompare(b[0]);
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });
  }
  return entries.map(([name, value]) => ({ name, value }));
}

export default function Dashboard() {
  const { user } = useAuth();
  const [inquiries, setInquiries] = useState([]);
  const [adminSummary, setAdminSummary] = useState(null);
  const [adminDashboard, setAdminDashboard] = useState(null);
  const [buyerStats, setBuyerStats] = useState({ rfqs: 0, cartItems: 0, wishlistItems: 0 });
  const [sellerStats, setSellerStats] = useState({ rfqs: 0, orders: 0 });
  const [buyerDashboard, setBuyerDashboard] = useState(null);
  const [sellerDashboard, setSellerDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [adminRfqTrends, setAdminRfqTrends] = useState([]);
  const [adminOrderTrends, setAdminOrderTrends] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        if (user?.role === 'admin') {
          const [summaryRes, dashboardRes, tr, tor] = await Promise.all([
            adminApi.summary().catch(() => ({ data: { data: { summary: null } } })),
            adminApi.dashboard().catch(() => ({ data: { data: { dashboard: null } } })),
            adminApi.getAnalyticsRfqTrends().catch(() => ({ data: { data: { rfqTrends: [] } } })),
            adminApi.getAnalyticsOrderTrends().catch(() => ({ data: { data: { orderTrends: [] } } })),
          ]);
          setAdminSummary(summaryRes.data?.data?.summary ?? null);
          setAdminDashboard(dashboardRes.data?.data?.dashboard ?? null);
          setAdminRfqTrends(tr.data?.data?.rfqTrends || []);
          setAdminOrderTrends(tor.data?.data?.orderTrends || []);
        } else if (user?.role === 'buyer') {
          const [dashRes, inqRes] = await Promise.all([
            buyerDashboardApi.get().then((r) => r.data.data?.dashboard).catch(() => null),
            inquiriesApi.getMe().then((r) => r.data.data.inquiries || []).catch(() => []),
          ]);
          setBuyerDashboard(dashRes || null);
          setInquiries(inqRes);
          if (dashRes) {
            setBuyerStats({
              rfqs: dashRes.rfqsCreated ?? 0,
              cartItems: dashRes.cartCount ?? 0,
              wishlistItems: dashRes.wishlistCount ?? 0,
            });
          } else {
            const [rfqRes, cartRes, wishRes] = await Promise.all([
              rfqApi.getMy().then((r) => r.data.data.rfqs || []).catch(() => []),
              cartApi.get().then((r) => r.data.data.items || []).catch(() => []),
              wishlistApi.get().then((r) => r.data.data.items || []).catch(() => []),
            ]);
            setBuyerStats({ rfqs: rfqRes.length, cartItems: cartRes.length, wishlistItems: wishRes.length });
          }
        } else if (user?.role === 'seller') {
          const [dashRes, inqRes] = await Promise.all([
            sellerDashboardApi.get().then((r) => r.data.data?.dashboard).catch(() => null),
            inquiriesApi.getMe().then((r) => r.data.data.inquiries || []).catch(() => []),
          ]);
          setSellerDashboard(dashRes || null);
          setInquiries(inqRes);
          if (dashRes) {
            setSellerStats({ rfqs: dashRes.activeRfqs ?? 0, orders: dashRes.ordersReceived ?? 0 });
          } else {
            const [rfqRes, ordersRes] = await Promise.all([
              rfqApi.getAssigned().then((r) => r.data.data.rfqs || []).catch(() => []),
              ordersApi.getMy().then((r) => r.data.data.orders || []).catch(() => []),
            ]);
            setSellerStats({ rfqs: rfqRes.length, orders: ordersRes.length });
          }
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

  const sellerRfqsByMonthData = useMemo(() => {
    const m = sellerDashboard?.rfqsByMonth;
    if (!m || typeof m !== 'object') return [];
    return Object.entries(m).map(([month, count]) => ({ month, count }));
  }, [sellerDashboard]);

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="h-36 rounded-3xl bg-slate-200 animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-slate-100 rounded-2xl border border-slate-200/80 animate-pulse" />
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

  const roleHero =
    user?.role === 'admin'
      ? 'border-l-4 border-rose-400'
      : user?.role === 'seller'
        ? 'border-l-4 border-indigo-400'
        : 'border-l-4 border-teal-400';

  const roleBlurb =
    user?.role === 'admin'
      ? 'Platform health, supplier verification, and marketplace velocity at a glance.'
      : user?.role === 'seller'
        ? 'Incoming demand on your catalog—RFQs, quotes, and orders in one narrative view.'
        : 'Your sourcing pipeline: inquiries, RFQs, quotes, and checkout-ready orders.';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="space-y-2">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className={`relative rounded-3xl bg-slate-900 text-white p-6 sm:p-9 mb-10 shadow-2xl shadow-slate-900/20 overflow-hidden ring-1 ring-white/10 ${roleHero}`}
      >
        <div className="absolute inset-0 bg-mesh-dark bg-mesh opacity-60" />
        <div className="absolute top-0 right-0 w-72 h-72 bg-teal-500/15 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative flex flex-col sm:flex-row sm:items-center gap-6">
          <div className="h-16 w-16 rounded-2xl bg-teal-500/25 flex items-center justify-center ring-1 ring-white/20 shrink-0">
            <Package className="h-9 w-9 text-teal-200" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-teal-300/90 text-xs font-semibold uppercase tracking-wider mb-1">
              {user?.role === 'admin' && 'Control center'}
              {user?.role === 'seller' && 'Seller workspace'}
              {user?.role === 'buyer' && 'Buyer command center'}
              {user?.role !== 'admin' && user?.role !== 'seller' && user?.role !== 'buyer' && 'Dashboard'}
            </p>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Hello, {user?.name}</h1>
            <p className="text-slate-300 text-sm mt-2 max-w-2xl leading-relaxed">{roleBlurb}</p>
          </div>
        </div>
      </motion.div>

      {user?.role === 'admin' && (adminSummary || adminDashboard) && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <StatCard title="Users" value={adminDashboard?.totalUsers ?? adminSummary?.users ?? 0} icon={Users} />
            <StatCard title="Products" value={adminDashboard?.totalProducts ?? adminSummary?.products ?? 0} icon={Package} />
            <StatCard title="Inquiries" value={adminSummary?.inquiries ?? 0} icon={MessageSquare} />
            {adminDashboard && (
              <>
                <StatCard title="Verified suppliers" value={adminDashboard.verifiedSuppliers} icon={Users} />
                <StatCard title="RFQs" value={adminDashboard.totalRfqs} icon={Activity} />
                <StatCard title="Orders" value={adminDashboard.totalOrders} icon={Package} />
              </>
            )}
          </div>
          {(adminDashboard?.rfqStatusDistribution && Object.keys(adminDashboard.rfqStatusDistribution).length > 0) ||
          (adminDashboard?.orderStatusDistribution && Object.keys(adminDashboard.orderStatusDistribution).length > 0) ? (
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {adminDashboard?.rfqStatusDistribution && Object.keys(adminDashboard.rfqStatusDistribution).length > 0 && (
                <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40">
                  <CardHeader>
                    <span className="section-heading block mb-1">Pipeline</span>
                    <span className="section-title">RFQ status distribution</span>
                  </CardHeader>
                  <CardBody className="h-64 chart-surface m-4 mt-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={distToPieData(adminDashboard.rfqStatusDistribution, RFQ_STATUS_PIPELINE)}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={88}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          {distToPieData(adminDashboard.rfqStatusDistribution, RFQ_STATUS_PIPELINE).map((_, i) => (
                            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardBody>
                </Card>
              )}
              {adminDashboard?.orderStatusDistribution && Object.keys(adminDashboard.orderStatusDistribution).length > 0 && (
                <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40">
                  <CardHeader>
                    <span className="section-heading block mb-1">Fulfillment</span>
                    <span className="section-title">Order status distribution</span>
                  </CardHeader>
                  <CardBody className="h-64 chart-surface m-4 mt-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={distToPieData(adminDashboard.orderStatusDistribution, ORDER_STATUS_PIPELINE)}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={88}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          {distToPieData(adminDashboard.orderStatusDistribution, ORDER_STATUS_PIPELINE).map((_, i) => (
                            <Cell key={i} fill={CHART_COLORS[(i + 2) % CHART_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardBody>
                </Card>
              )}
            </div>
          ) : null}
          {(adminRfqTrends.length > 0 || adminOrderTrends.length > 0) && (
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {adminRfqTrends.length > 0 && (
                <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40">
                  <CardHeader>
                    <span className="section-heading block mb-1">Trend</span>
                    <span className="section-title">RFQ volume by month</span>
                  </CardHeader>
                  <CardBody className="h-64 chart-surface m-4 mt-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={adminRfqTrends}>
                        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#0d9488" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardBody>
                </Card>
              )}
              {adminOrderTrends.length > 0 && (
                <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40">
                  <CardHeader>
                    <span className="section-heading block mb-1">Trend</span>
                    <span className="section-title">Order volume by month</span>
                  </CardHeader>
                  <CardBody className="h-64 chart-surface m-4 mt-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={adminOrderTrends}>
                        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardBody>
                </Card>
              )}
            </div>
          )}
          {adminDashboard?.topSuppliers?.length > 0 && (
            <Card className="mb-6 border-slate-200/90 shadow-md">
              <CardHeader>
                <span className="section-heading block mb-1">Leaders</span>
                <span className="section-title">Top suppliers</span>
              </CardHeader>
              <CardBody>
                <ul className="space-y-0 divide-y divide-slate-100">
                  {adminDashboard.topSuppliers.slice(0, 5).map((s) => (
                    <li key={s.sellerId} className="flex flex-wrap items-center justify-between gap-2 py-3 first:pt-0">
                      <span className="font-medium text-slate-800">{s.name || s.email || s.sellerId}</span>
                      <Badge variant={s.verified ? 'success' : 'outline'} className="font-semibold tabular-nums">
                        {s.orderCount} orders · {s.trustScore} trust
                      </Badge>
                    </li>
                  ))}
                </ul>
              </CardBody>
            </Card>
          )}
          {adminDashboard?.topCategories?.length > 0 && (
            <Card className="mb-6 border-slate-200/90 shadow-md">
              <CardHeader>
                <span className="section-heading block mb-1">Demand</span>
                <span className="section-title">Top categories</span>
              </CardHeader>
              <CardBody>
                <div className="flex flex-wrap gap-2">
                  {adminDashboard.topCategories.slice(0, 8).map((c) => (
                    <Badge key={c.name} variant="teal" className="font-semibold">
                      {c.name} ({c.count})
                    </Badge>
                  ))}
                </div>
              </CardBody>
            </Card>
          )}
          <Card className="mb-8 border-slate-200/90 shadow-md">
            <CardHeader className="flex flex-row items-center justify-between gap-4">
              <div>
                <span className="section-heading block mb-1">Audit</span>
                <span className="section-title">Recent admin activity</span>
              </div>
              <Link to="/admin/panel" className="text-sm font-semibold text-teal-600 hover:text-teal-700 shrink-0">
                Full logs →
              </Link>
            </CardHeader>
            <CardBody>
              {adminDashboard?.recentLogs?.length > 0 ? (
                <ul className="space-y-0 divide-y divide-slate-100">
                  {adminDashboard.recentLogs.slice(0, 8).map((log) => (
                    <li key={log.id || log._id} className="py-3 first:pt-0 flex flex-col gap-1">
                      <span className="font-semibold text-slate-900">{log.action || log.actionType}</span>
                      <div className="flex flex-wrap gap-x-3 text-xs text-slate-500">
                        <span>{log.actor || 'Admin'}</span>
                        <span className="tabular-nums">{log.createdAt ? new Date(log.createdAt).toLocaleString() : ''}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500">Open the Admin Panel → Activity Logs tab for full history.</p>
              )}
            </CardBody>
          </Card>
        </>
      )}

      {(user?.role === 'buyer' || user?.role === 'seller') && (
        <>
          <div className="mb-6">
            <p className="section-heading mb-2">Snapshot</p>
            <p className="text-sm text-slate-500 max-w-2xl">
              {user?.role === 'buyer'
                ? 'Track sourcing momentum: inquiries in flight, RFQ cart depth, and order outcomes.'
                : 'Monitor pipeline pressure: catalog coverage, assigned RFQs, and revenue-bearing orders.'}
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard title="Total inquiries" value={inquiries.length} icon={MessageSquare} />
            <StatCard title="Pending" value={inquiries.filter((i) => i.status === 'pending').length} icon={Activity} />
            {user?.role === 'buyer' && (
              <>
                <StatCard title="RFQs created" value={buyerStats.rfqs} icon={Activity} />
                <StatCard title="Quotes received" value={buyerDashboard?.quotesReceived ?? '—'} icon={MessageSquare} />
                <StatCard title="Orders placed" value={buyerDashboard?.ordersPlaced ?? '—'} icon={Package} />
                <StatCard title="Cart" value={buyerStats.cartItems} icon={Package} />
                <StatCard title="Wishlist" value={buyerStats.wishlistItems} icon={Package} />
              </>
            )}
            {user?.role === 'seller' && (
              <>
                <StatCard title="Products" value={sellerDashboard?.totalProducts ?? '—'} icon={Package} />
                <StatCard title="Active RFQs" value={sellerStats.rfqs} icon={TrendingUp} />
                <StatCard title="Quotes submitted" value={sellerDashboard?.totalQuotesSubmitted ?? '—'} icon={Activity} />
                <StatCard title="Orders received" value={sellerStats.orders} icon={Package} />
              </>
            )}
          </div>
          {user?.role === 'buyer' && buyerDashboard?.rfqStatusDistribution && Object.keys(buyerDashboard.rfqStatusDistribution).length > 0 && (
            <Card className="mb-8 border-slate-200/90 shadow-lg">
              <CardHeader>
                <span className="section-heading block mb-1">Your pipeline</span>
                <span className="section-title">RFQs by status</span>
              </CardHeader>
              <CardBody className="h-56 chart-surface m-4 mt-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distToPieData(buyerDashboard.rfqStatusDistribution, RFQ_STATUS_PIPELINE)}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={72}
                    >
                      {distToPieData(buyerDashboard.rfqStatusDistribution, RFQ_STATUS_PIPELINE).map((_, i) => (
                        <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardBody>
            </Card>
          )}
          {user?.role === 'seller' && sellerRfqsByMonthData.length > 0 && (
            <Card className="mb-8 border-slate-200/90 shadow-lg">
              <CardHeader>
                <span className="section-heading block mb-1">Demand on your SKUs</span>
                <span className="section-title">RFQs by month</span>
              </CardHeader>
              <CardBody className="h-56 chart-surface m-4 mt-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={sellerRfqsByMonthData}>
                    <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0d9488" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardBody>
            </Card>
          )}
          {user?.role === 'seller' && sellerDashboard?.ordersByStatus && Object.keys(sellerDashboard.ordersByStatus).length > 0 && (
            <Card className="mb-8 border-slate-200/90 shadow-lg">
              <CardHeader>
                <span className="section-heading block mb-1">Fulfillment mix</span>
                <span className="section-title">Orders by status</span>
              </CardHeader>
              <CardBody className="h-56 chart-surface m-4 mt-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distToPieData(sellerDashboard.ordersByStatus, ORDER_STATUS_PIPELINE)}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={72}
                    >
                      {distToPieData(sellerDashboard.ordersByStatus, ORDER_STATUS_PIPELINE).map((_, i) => (
                        <Cell key={i} fill={CHART_COLORS[(i + 1) % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardBody>
            </Card>
          )}
          {user?.role === 'buyer' && (buyerDashboard?.recentRfqs?.length > 0 || buyerDashboard?.recentOrders?.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {buyerDashboard.recentRfqs?.length > 0 && (
                <Card className="border-slate-200/90 shadow-md">
                  <CardHeader>
                    <span className="section-heading block mb-1">Latest</span>
                    <span className="section-title">Recent RFQs</span>
                  </CardHeader>
                  <CardBody>
                    <ul className="space-y-0 divide-y divide-slate-100">
                      {buyerDashboard.recentRfqs.slice(0, 5).map((r) => (
                        <li key={r.id || r._id} className="py-3 first:pt-0 flex flex-wrap items-center justify-between gap-2">
                          <Link to={`/rfq/${r.id || r._id}`} className="font-semibold text-teal-700 hover:text-teal-800">
                            RFQ #{String(r.id || r._id).slice(-6)}
                          </Link>
                          <Badge variant="default" className="capitalize font-semibold">{r.status}</Badge>
                        </li>
                      ))}
                    </ul>
                  </CardBody>
                </Card>
              )}
              {buyerDashboard.recentOrders?.length > 0 && (
                <Card className="border-slate-200/90 shadow-md">
                  <CardHeader>
                    <span className="section-heading block mb-1">Checkout</span>
                    <span className="section-title">Recent orders</span>
                  </CardHeader>
                  <CardBody>
                    <ul className="space-y-0 divide-y divide-slate-100">
                      {buyerDashboard.recentOrders.slice(0, 5).map((o) => (
                        <li key={o.id || o._id} className="py-3 first:pt-0 flex flex-wrap items-center justify-between gap-2">
                          <Link to={`/orders/${o.id || o._id}`} className="font-semibold text-teal-700 hover:text-teal-800">
                            Order #{String(o.id || o._id).slice(-6)}
                          </Link>
                          <Badge variant="default" className="capitalize font-semibold">{o.status}</Badge>
                        </li>
                      ))}
                    </ul>
                  </CardBody>
                </Card>
              )}
            </div>
          )}
          <Card className="border-slate-200/90 shadow-lg shadow-slate-200/30">
            <CardHeader>
              <span className="section-heading block mb-1">Conversations</span>
              <h2 className="section-title">
                {user?.role === 'buyer' ? 'My inquiries' : 'Inquiries on my products'}
              </h2>
            </CardHeader>
            <CardBody>
              {inquiries.length === 0 ? (
                <EmptyState
                  icon={MessageSquare}
                  title="No inquiries yet"
                  description={user?.role === 'buyer' ? 'Send product inquiries from detail pages—they land here for follow-up.' : 'When buyers message your listings, threads appear here.'}
                />
              ) : (
                <div className="space-y-3">
                  {inquiries.map((inq, i) => (
                    <motion.div
                      key={inq._id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl border border-slate-200/90 bg-slate-50/40 hover:bg-white hover:shadow-md hover:border-teal-200/60 transition-all"
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
          <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-5 mt-8">
            <p className="section-heading mb-3">Quick links</p>
            <div className="flex flex-wrap gap-3">
              {user?.role === 'buyer' && (
                <>
                  <Link to="/cart" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-teal-700 shadow-sm ring-1 ring-slate-200 hover:ring-teal-200 transition-all">
                    <ArrowRight className="h-4 w-4" /> RFQ Cart
                  </Link>
                  <Link to="/wishlist" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-teal-700 shadow-sm ring-1 ring-slate-200 hover:ring-teal-200 transition-all">
                    <ArrowRight className="h-4 w-4" /> Wishlist
                  </Link>
                  <Link to="/rfq" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-teal-700 shadow-sm ring-1 ring-slate-200 hover:ring-teal-200 transition-all">
                    <ArrowRight className="h-4 w-4" /> My RFQs
                  </Link>
                </>
              )}
              {user?.role === 'seller' && (
                <>
                  <Link to="/seller/products" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-700 shadow-sm ring-1 ring-slate-200 hover:ring-indigo-200 transition-all">
                    <ArrowRight className="h-4 w-4" /> Manage products
                  </Link>
                  <Link to="/seller/rfqs" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-700 shadow-sm ring-1 ring-slate-200 hover:ring-indigo-200 transition-all">
                    <ArrowRight className="h-4 w-4" /> Assigned RFQs
                  </Link>
                  <Link to="/orders" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-700 shadow-sm ring-1 ring-slate-200 hover:ring-indigo-200 transition-all">
                    <ArrowRight className="h-4 w-4" /> My orders
                  </Link>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </motion.div>
  );
}
