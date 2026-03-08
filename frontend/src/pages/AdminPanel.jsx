import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, FolderOpen, FileText, Package, Activity, LayoutDashboard, ShieldCheck } from 'lucide-react';
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
      const [d, u, c, r, o, l] = await Promise.all([
        adminApi.dashboard().then((res) => res.data.data.dashboard).catch(() => null),
        adminApi.getUsers().then((res) => res.data.data.users),
        categoriesApi.list().then((res) => res.data.data.categories),
        adminApi.getRfqs().then((res) => res.data.data.rfqs),
        adminApi.getOrders().then((res) => res.data.data.orders),
        adminApi.getLogs().then((res) => res.data.data.logs),
      ]);
      setDashboard(d || null);
      setUsers(u || []);
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
      await adminApi.verifySupplier(userId, verified);
      toast.add(verified ? 'Supplier verified' : 'Verification removed', 'success');
      load(); // refresh so trust score updates
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

  if (loading && !users.length && !dashboard) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-2xl font-bold mb-6">Admin Panel</h1>
      <div className="flex gap-2 border-b border-neutral-200 mb-6 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 whitespace-nowrap ${
              tab === t.id ? 'border-primary-600 text-primary-600' : 'border-transparent text-neutral-600'
            }`}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'dashboard' && dashboard && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-6">
          <Card className="p-4">
            <p className="text-sm text-neutral-500">Total users</p>
            <p className="text-2xl font-bold text-neutral-900">{dashboard.totalUsers ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-neutral-500">Verified suppliers</p>
            <p className="text-2xl font-bold text-green-600">{dashboard.verifiedSuppliers ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-neutral-500">Pending suppliers</p>
            <p className="text-2xl font-bold text-amber-600">{dashboard.pendingSuppliers ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-neutral-500">Total RFQs</p>
            <p className="text-2xl font-bold text-neutral-900">{dashboard.totalRfqs ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-neutral-500">Total quotes</p>
            <p className="text-2xl font-bold text-neutral-900">{dashboard.totalQuotes ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-neutral-500">Total orders</p>
            <p className="text-2xl font-bold text-neutral-900">{dashboard.totalOrders ?? 0}</p>
          </Card>
        </div>
      )}

      {tab === 'suppliers' && (
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Name</th>
                  <th className="text-left p-3">Email</th>
                  <th className="text-left p-3">Trust score</th>
                  <th className="text-left p-3">Verified</th>
                  <th className="text-left p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.filter((u) => u.role === 'seller').map((u) => (
                  <tr key={u._id} className="border-b">
                    <td className="p-3">{u.name}</td>
                    <td className="p-3">{u.email}</td>
                    <td className="p-3">
                      {u.trustScore != null ? `${Math.round(u.trustScore)}%` : '—'}
                      {u.trustLevel && <span className="text-neutral-500 text-xs ml-1">({u.trustLevel})</span>}
                    </td>
                    <td className="p-3">{u.isVerifiedSupplier ? <Badge variant="success">Verified</Badge> : <Badge variant="default">Pending</Badge>}</td>
                    <td className="p-3 flex gap-2">
                      <Button size="sm" variant="secondary" onClick={() => handleVerify(u._id, !u.isVerifiedSupplier)}>
                        {u.isVerifiedSupplier ? 'Unverify' : 'Verify'}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleRecalculateScore(u._id)}>Recalculate score</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'users' && (
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Name</th>
                  <th className="text-left p-3">Email</th>
                  <th className="text-left p-3">Role</th>
                  <th className="text-left p-3">Trust score</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-left p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u._id} className="border-b">
                    <td className="p-3">{u.name}</td>
                    <td className="p-3">{u.email}</td>
                    <td className="p-3">{u.role}</td>
                    <td className="p-3">
                      {u.role === 'seller' && (u.trustScore != null ? `${Math.round(u.trustScore)}% (${u.trustLevel || '—'})` : '—')}
                      {u.role !== 'seller' && '—'}
                    </td>
                    <td className="p-3">
                      {u.isBanned && <Badge variant="danger">Banned</Badge>}
                      {u.role === 'seller' && u.isVerifiedSupplier && <Badge variant="success">Verified</Badge>}
                    </td>
                    <td className="p-3 flex gap-2">
                      {u.role !== 'admin' && (
                        <Button size="sm" variant="secondary" onClick={() => handleBan(u._id, !u.isBanned)}>
                          {u.isBanned ? 'Unban' : 'Ban'}
                        </Button>
                      )}
                      {u.role === 'seller' && (
                        <Button size="sm" variant="secondary" onClick={() => handleVerify(u._id, !u.isVerifiedSupplier)}>
                          {u.isVerifiedSupplier ? 'Unverify' : 'Verify'}
                        </Button>
                      )}
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
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">RFQ ID</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-left p-3">Items</th>
                </tr>
              </thead>
              <tbody>
                {rfqs.map((r) => (
                  <tr key={r._id} className="border-b">
                    <td className="p-3">#{r._id.slice(-6)}</td>
                    <td className="p-3"><Badge>{r.status}</Badge></td>
                    <td className="p-3">{r.items?.length || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'orders' && (
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Order ID</th>
                  <th className="text-left p-3">Buyer</th>
                  <th className="text-left p-3">Total</th>
                  <th className="text-left p-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o._id} className="border-b">
                    <td className="p-3">#{o._id.slice(-6)}</td>
                    <td className="p-3">{o.buyerId?.name}</td>
                    <td className="p-3">₹{o.totalAmount}</td>
                    <td className="p-3"><Badge>{o.status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'logs' && (
        <Card>
          <ul className="divide-y max-h-96 overflow-y-auto">
            {logs.map((log) => (
              <li key={log._id} className="p-4 text-sm">
                <span className="text-neutral-500">{new Date(log.createdAt).toLocaleString()}</span>
                <span className="ml-2 font-medium">{log.actionType}</span>
                <span className="ml-2 text-neutral-600">{JSON.stringify(log.details || {})}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </motion.div>
  );
}
