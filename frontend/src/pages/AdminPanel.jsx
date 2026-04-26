import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Users, FolderOpen, FileText, Package, Activity, LayoutDashboard, ShieldCheck, Settings2 } from 'lucide-react';
import { adminApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { categoriesApi } from '../api/client';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'suppliers', label: 'Supplier verification', icon: ShieldCheck },
  { id: 'categories', label: 'Categories', icon: FolderOpen },
  { id: 'rfqs', label: 'RFQs', icon: FileText },
  { id: 'orders', label: 'Orders', icon: Package },
  { id: 'logs', label: 'Activity Logs', icon: Activity },
];

export default function AdminPanel() {
  const [tab, setTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [rfqs, setRfqs] = useState([]);
  const [orders, setOrders] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categoryForm, setCategoryForm] = useState({ name: '', slug: '' });
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [d, u, sup, c, r, o, l] = await Promise.all([
        adminApi.dashboard().then((res) => res.data.data.dashboard).catch(() => null),
        adminApi.getUsers().then((res) => res.data.data.users),
        adminApi.getSuppliers().then((res) => res.data.data.suppliers).catch(() => []),
        adminApi.getCategories().then((res) => res.data.data.categories || []).catch(() => []),
        adminApi.getRfqs().then((res) => res.data.data.rfqs),
        adminApi.getOrders().then((res) => res.data.data.orders),
        adminApi.getLogs().then((res) => res.data.data.logs),
      ]);
      setDashboard(d || null);
      setUsers(u || []);
      setSuppliers(sup || []);
      setCategories(c || []);
      setRfqs(r || []);
      setOrders(o || []);
      setLogs(l || []);
    } catch {
      toast.add('Failed to load admin data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleBan = async (userId, banned) => {
    try {
      if (banned) await adminApi.banUser(userId, true);
      else await adminApi.unbanUser(userId);
      setUsers((prev) => prev.map((u) => (u._id === userId ? { ...u, isBanned: banned } : u)));
      toast.add(banned ? 'User banned' : 'User unbanned', 'success');
    } catch {
      toast.add('Action failed', 'error');
    }
  };

  const handleRecalculateScore = async (sellerId) => {
    try {
      await adminApi.recalculateScore(sellerId);
      toast.add('Trust score recalculated', 'success');
      load();
    } catch {
      toast.add('Recalculate failed', 'error');
    }
  };

  const handleVerify = async (userId, verified) => {
    try {
      if (verified) {
        await adminApi.verifySupplier(userId, true);
      } else {
        try {
          await adminApi.unverifySupplier(userId);
        } catch {
          await adminApi.verifySupplier(userId, false);
        }
      }
      toast.add(verified ? 'Supplier verified' : 'Verification removed', 'success');
      load();
    } catch {
      toast.add('Action failed', 'error');
    }
  };

  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    try {
      await categoriesApi.create({ name: categoryForm.name, slug: categoryForm.slug || categoryForm.name.toLowerCase().replace(/\s+/g, '-') });
      toast.add('Category created', 'success');
      setCategoryForm({ name: '', slug: '' });
      load();
    } catch {
      toast.add('Failed to create category', 'error');
    }
  };

  const handleCategoryDelete = async (id) => {
    if (!window.confirm('Delete this category?')) return;
    try {
      await categoriesApi.delete(id);
      toast.add('Category deleted', 'success');
      load();
    } catch {
      toast.add('Failed to delete', 'error');
    }
  };

  if (loading && !users.length && !dashboard) {
    return (
      <div className="space-y-6">
        <div className="h-24 rounded-3xl bg-slate-200 animate-pulse" />
        <div className="h-12 rounded-xl bg-slate-100 animate-pulse max-w-lg" />
        <div className="h-64 rounded-2xl bg-slate-100 animate-pulse" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 max-w-[100rem]">
      <div className="relative overflow-hidden rounded-3xl bg-slate-900 text-white p-6 sm:p-8 shadow-2xl shadow-slate-900/20 ring-1 ring-white/10 border-l-4 border-rose-400">
        <div className="absolute inset-0 bg-mesh-dark opacity-50" />
        <div className="absolute top-0 right-0 w-72 h-72 bg-rose-500/10 rounded-full blur-3xl" />
        <div className="relative flex flex-col sm:flex-row sm:items-center gap-4 sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="h-14 w-14 rounded-2xl bg-white/10 flex items-center justify-center ring-1 ring-white/20">
              <Settings2 className="h-7 w-7 text-rose-200" />
            </div>
            <div>
              <p className="text-rose-200/90 text-xs font-semibold uppercase tracking-wider">Operations</p>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mt-1">Admin control center</h1>
              <p className="text-slate-400 text-sm mt-2 max-w-xl">
                Users, supplier verification, catalog, RFQs, orders, and immutable activity logs—high-impact actions are visually separated.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 p-1.5 rounded-2xl bg-slate-100/90 ring-1 ring-slate-200/80 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
              tab === t.id
                ? 'bg-white text-teal-800 shadow-md shadow-slate-200/50 ring-1 ring-slate-200/80'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <t.icon className="h-4 w-4 shrink-0" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'dashboard' && dashboard && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-6">
          <Card className="p-5 border-slate-200/90 shadow-md">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total users</p>
            <p className="text-3xl font-bold text-slate-900 mt-2 tabular-nums">{dashboard.totalUsers ?? 0}</p>
          </Card>
          <Card className="p-5 border-slate-200/90 shadow-md ring-1 ring-emerald-100/80 bg-emerald-50/20">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800/80">Verified suppliers</p>
            <p className="text-3xl font-bold text-emerald-700 mt-2 tabular-nums">{dashboard.verifiedSuppliers ?? 0}</p>
          </Card>
          <Card className="p-5 border-slate-200/90 shadow-md ring-1 ring-amber-100/80 bg-amber-50/20">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-900/70">Pending suppliers</p>
            <p className="text-3xl font-bold text-amber-700 mt-2 tabular-nums">{dashboard.pendingSuppliers ?? 0}</p>
          </Card>
          <Card className="p-5 border-slate-200/90 shadow-md">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total RFQs</p>
            <p className="text-3xl font-bold text-slate-900 mt-2 tabular-nums">{dashboard.totalRfqs ?? 0}</p>
          </Card>
          <Card className="p-5 border-slate-200/90 shadow-md">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total quotes</p>
            <p className="text-3xl font-bold text-slate-900 mt-2 tabular-nums">{dashboard.totalQuotes ?? 0}</p>
          </Card>
          <Card className="p-5 border-slate-200/90 shadow-md">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total orders</p>
            <p className="text-3xl font-bold text-slate-900 mt-2 tabular-nums">{dashboard.totalOrders ?? 0}</p>
          </Card>
        </div>
      )}

      {tab === 'suppliers' && (
        <Card className="border-slate-200/90 shadow-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
            <p className="section-heading mb-1">Governance</p>
            <p className="section-title">Supplier verification</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="text-left p-4 font-semibold">Name</th>
                  <th className="text-left p-4 font-semibold">Email</th>
                  <th className="text-left p-4 font-semibold">Company / City</th>
                  <th className="text-left p-4 font-semibold">Trust score</th>
                  <th className="text-left p-4 font-semibold">Verified</th>
                  <th className="text-left p-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(suppliers.length > 0 ? suppliers : users.filter((u) => u.role === 'seller')).map((u) => {
                  const uid = u._id || u.id;
                  return (
                    <tr key={uid} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-4 font-medium text-slate-900">{u.name}</td>
                      <td className="p-4 text-slate-600">{u.email}</td>
                      <td className="p-4 text-slate-600">{u.companyName || '—'} {u.city ? ` · ${u.city}` : ''}</td>
                      <td className="p-4 tabular-nums text-slate-800">
                        {u.trustScore != null ? `${Math.round(u.trustScore)}` : '—'}
                        {u.trustLevel && <span className="text-slate-400 text-xs ml-1">({u.trustLevel})</span>}
                      </td>
                      <td className="p-4">{u.isVerifiedSupplier ? <Badge variant="success">Verified</Badge> : <Badge variant="warning">Pending</Badge>}</td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-2">
                          {u.isVerifiedSupplier ? (
                            <Button size="sm" variant="outlineDanger" className="rounded-lg" onClick={() => handleVerify(uid, !u.isVerifiedSupplier)}>
                              Remove verification
                            </Button>
                          ) : (
                            <Button size="sm" variant="successSolid" className="rounded-lg" onClick={() => handleVerify(uid, !u.isVerifiedSupplier)}>
                              Verify supplier
                            </Button>
                          )}
                          <Button size="sm" variant="ghost" className="rounded-lg text-slate-600" onClick={() => handleRecalculateScore(uid)}>
                            Recalculate score
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'users' && (
        <Card className="border-slate-200/90 shadow-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
            <p className="section-heading mb-1">Directory</p>
            <p className="section-title">All users</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="text-left p-4 font-semibold">Name</th>
                  <th className="text-left p-4 font-semibold">Email</th>
                  <th className="text-left p-4 font-semibold">Role</th>
                  <th className="text-left p-4 font-semibold">Trust score</th>
                  <th className="text-left p-4 font-semibold">Status</th>
                  <th className="text-left p-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u._id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-4 font-medium text-slate-900">{u.name}</td>
                    <td className="p-4 text-slate-600">{u.email}</td>
                    <td className="p-4 capitalize text-slate-700">{u.role}</td>
                    <td className="p-4 text-slate-700 tabular-nums">
                      {u.role === 'seller' && (u.trustScore != null ? `${Math.round(u.trustScore)}% (${u.trustLevel || '—'})` : '—')}
                      {u.role !== 'seller' && '—'}
                    </td>
                    <td className="p-4">
                      {u.isBanned && <Badge variant="danger">Banned</Badge>}
                      {u.role === 'seller' && u.isVerifiedSupplier && <Badge variant="success" className="ml-1">Verified</Badge>}
                    </td>
                    <td className="p-4">
                      <div className="flex flex-wrap gap-2">
                        {u.role !== 'admin' &&
                          (u.isBanned ? (
                            <Button size="sm" variant="secondary" className="rounded-lg" onClick={() => handleBan(u._id, !u.isBanned)}>
                              Unban user
                            </Button>
                          ) : (
                            <Button size="sm" variant="outlineDanger" className="rounded-lg" onClick={() => handleBan(u._id, !u.isBanned)}>
                              Ban user
                            </Button>
                          ))}
                        {u.role === 'seller' &&
                          (u.isVerifiedSupplier ? (
                            <Button size="sm" variant="outlineDanger" className="rounded-lg" onClick={() => handleVerify(u._id, !u.isVerifiedSupplier)}>
                              Unverify
                            </Button>
                          ) : (
                            <Button size="sm" variant="successSolid" className="rounded-lg" onClick={() => handleVerify(u._id, !u.isVerifiedSupplier)}>
                              Verify
                            </Button>
                          ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'categories' && (
        <div className="space-y-4">
          <Card>
            <form onSubmit={handleCategorySubmit} className="p-4 flex flex-wrap gap-2 items-end">
              <Input label="Name" value={categoryForm.name} onChange={(e) => setCategoryForm((f) => ({ ...f, name: e.target.value }))} required />
              <Input label="Slug" value={categoryForm.slug} onChange={(e) => setCategoryForm((f) => ({ ...f, slug: e.target.value }))} placeholder="auto" />
              <Button type="submit">Add category</Button>
            </form>
          </Card>
          <Card>
            <ul className="divide-y">
              {categories.map((c) => (
                <li key={c._id} className="p-4 flex justify-between">
                  <span>{c.name}</span>
                  <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleCategoryDelete(c._id)}>Delete</Button>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      {tab === 'rfqs' && (
        <Card className="border-slate-200/90 shadow-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
            <p className="section-title">RFQs</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
                  <th className="text-left p-4 font-semibold">RFQ ID</th>
                  <th className="text-left p-4 font-semibold">Status</th>
                  <th className="text-left p-4 font-semibold">Items</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rfqs.map((r) => (
                  <tr key={r._id} className="hover:bg-slate-50/80">
                    <td className="p-4 font-mono text-xs font-semibold">#{r._id.slice(-6)}</td>
                    <td className="p-4"><Badge className="capitalize font-semibold">{r.status}</Badge></td>
                    <td className="p-4 tabular-nums">{r.items?.length || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'orders' && (
        <Card className="border-slate-200/90 shadow-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
            <p className="section-title">Orders</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
                  <th className="text-left p-4 font-semibold">Order ID</th>
                  <th className="text-left p-4 font-semibold">Buyer</th>
                  <th className="text-left p-4 font-semibold">Total</th>
                  <th className="text-left p-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {orders.map((o) => (
                  <tr key={o._id} className="hover:bg-slate-50/80">
                    <td className="p-4">
                      <Link to={`/orders/${o._id}`} className="font-semibold text-teal-700 hover:text-teal-800 font-mono text-xs">
                        #{o._id.slice(-6)}
                      </Link>
                    </td>
                    <td className="p-4 text-slate-700">{o.buyerId?.name}</td>
                    <td className="p-4 font-semibold tabular-nums">₹{o.totalAmount}</td>
                    <td className="p-4"><Badge className="capitalize font-semibold">{o.status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'logs' && (
        <Card className="border-slate-200/90 shadow-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex flex-wrap justify-between gap-2">
            <div>
              <p className="section-heading mb-1">Immutable</p>
              <p className="section-title">Activity logs</p>
            </div>
            <p className="text-xs text-slate-500 self-end max-w-xs">Sticky header while scrolling wide tables.</p>
          </div>
          <div className="overflow-x-auto max-h-[36rem] overflow-y-auto">
            <table className="min-w-full text-sm">
              <thead className="sticky top-0 z-10 bg-slate-100 shadow-sm border-b border-slate-200">
                <tr className="text-xs uppercase tracking-wider text-slate-600">
                  <th className="text-left p-4 font-semibold">Action</th>
                  <th className="text-left p-4 font-semibold">Actor</th>
                  <th className="text-left p-4 font-semibold">Role</th>
                  <th className="text-left p-4 font-semibold">Target</th>
                  <th className="text-left p-4 font-semibold whitespace-nowrap">When</th>
                  <th className="text-left p-4 font-semibold">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log._id || log.id} className="hover:bg-teal-50/30 odd:bg-slate-50/40">
                    <td className="p-4 font-semibold text-slate-900 align-top">{log.action || log.actionType}</td>
                    <td className="p-4 text-slate-700 align-top">{log.actor || log.adminId?.name || '—'}</td>
                    <td className="p-4 align-top"><Badge variant="outline" className="text-[10px]">{log.actorRole || 'admin'}</Badge></td>
                    <td className="p-4 text-xs text-slate-600 align-top font-mono">{log.targetType || '—'} · {log.targetId || '—'}</td>
                    <td className="p-4 text-slate-500 whitespace-nowrap align-top text-xs tabular-nums">{log.createdAt ? new Date(log.createdAt).toLocaleString() : '—'}</td>
                    <td className="p-4 text-xs text-slate-600 max-w-[14rem] align-top break-all" title={typeof log.details === 'object' ? JSON.stringify(log.details) : log.details}>
                      {typeof log.details === 'object' ? JSON.stringify(log.details) : log.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </motion.div>
  );
}
