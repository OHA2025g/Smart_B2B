import { formatDateTimeIst } from '../lib/istTime';
import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Users, FolderOpen, FileText, Package, Activity, LayoutDashboard, ShieldCheck, Settings2, Flag, X, ExternalLink, Search, CreditCard } from 'lucide-react';
import { adminApi, categoriesApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'users', label: 'Buyers', icon: Users },
  { id: 'suppliers', label: 'Supplier verification', icon: ShieldCheck },
  { id: 'categories', label: 'Categories', icon: FolderOpen },
  { id: 'rfqs', label: 'RFQs', icon: FileText },
  { id: 'orders', label: 'Orders', icon: Package },
  { id: 'billing', label: 'Billing & revenue', icon: CreditCard },
  { id: 'moderation', label: 'Moderation', icon: Flag },
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
  const [flaggedMessages, setFlaggedMessages] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [payments, setPayments] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [categoryForm, setCategoryForm] = useState({ name: '', slug: '' });
  const [profileDetail, setProfileDetail] = useState(null);
  const [profileDetailOpen, setProfileDetailOpen] = useState(false);
  const [profileDetailLoading, setProfileDetailLoading] = useState(false);
  const [buyerSearch, setBuyerSearch] = useState('');
  const [supplierSearch, setSupplierSearch] = useState('');
  const toast = useToast();

  const filteredBuyers = useMemo(() => {
    const q = buyerSearch.trim().toLowerCase();
    if (!q) return users;
    return users.filter((u) => {
      const blob = [u.name, u.email, u._id && String(u._id)]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return blob.includes(q);
    });
  }, [users, buyerSearch]);

  const filteredSuppliers = useMemo(() => {
    const q = supplierSearch.trim().toLowerCase();
    if (!q) return suppliers;
    return suppliers.filter((u) => {
      const blob = [
        u.name,
        u.email,
        u.companyName,
        u.gstNumber,
        u.city,
        u.state,
        u.country,
        u.phone,
        u.website,
        u.description,
        u._id && String(u._id),
        u.id && String(u.id),
        u.trustLevel != null && String(u.trustLevel),
        u.trustScore != null && String(u.trustScore),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return blob.includes(q);
    });
  }, [suppliers, supplierSearch]);

  const load = async () => {
    setLoading(true);
    try {
      const [d, u, sup, c, r, o, l, mm, sub, pay, rev] = await Promise.all([
        adminApi.dashboard().then((res) => res.data.data.dashboard).catch(() => null),
        adminApi.getUsers().then((res) => res.data.data.users),
        adminApi.getSuppliers().then((res) => res.data.data.suppliers).catch(() => []),
        adminApi.getCategories().then((res) => res.data.data.categories || []).catch(() => []),
        adminApi.getRfqs().then((res) => res.data.data.rfqs),
        adminApi.getOrders().then((res) => res.data.data.orders),
        adminApi.getLogs().then((res) => res.data.data.logs),
        adminApi.getModerationMessages().then((res) => res.data.data.messages || []).catch(() => []),
        adminApi.getSubscriptions().then((res) => res.data.data.subscriptions || []).catch(() => []),
        adminApi.getPayments().then((res) => res.data.data.payments || []).catch(() => []),
        adminApi.getRevenueSummary().then((res) => res.data.data.revenue).catch(() => null),
      ]);
      setDashboard(d || null);
      setUsers(u || []);
      setSuppliers(sup || []);
      setCategories(c || []);
      setRfqs(r || []);
      setOrders(o || []);
      setLogs(l || []);
      setFlaggedMessages(Array.isArray(mm) ? mm : []);
      setSubscriptions(sub || []);
      setPayments(pay || []);
      setRevenue(rev || null);
    } catch {
      toast.add('Failed to load admin data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // Initial load only; tab actions call load() explicitly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleBan = async (userId, banned) => {
    try {
      if (banned) await adminApi.banUser(userId, true);
      else await adminApi.unbanUser(userId);
      setUsers((prev) => prev.map((u) => (u._id === userId ? { ...u, isBanned: banned } : u)));
      setSuppliers((prev) =>
        prev.map((s) => {
          const id = s._id || s.id;
          if (String(id) !== String(userId)) return s;
          return { ...s, isBanned: banned };
        })
      );
      if (profileDetail?.user) {
        const pid = profileDetail.user._id || profileDetail.user.id;
        if (String(pid) === String(userId)) {
          setProfileDetail((d) => (d ? { ...d, user: { ...d.user, isBanned: banned } } : d));
        }
      }
      toast.add(banned ? 'User banned' : 'User unbanned', 'success');
    } catch {
      toast.add('Action failed', 'error');
    }
  };

  const handleRecalculateScore = async (sellerId) => {
    try {
      const { data } = await adminApi.recalculateScore(sellerId);
      const sc = data.data?.score;
      if (sc) {
        setSuppliers((prev) =>
          prev.map((s) => {
            const id = s._id || s.id;
            if (id !== sellerId) return s;
            return { ...s, trustScore: sc.total_score, trustLevel: sc.trust_level };
          })
        );
      } else {
        load();
      }
      toast.add('Trust score recalculated', 'success');
    } catch {
      toast.add('Recalculate failed', 'error');
    }
  };

  const openUserProfile = async (userId) => {
    setProfileDetailOpen(true);
    setProfileDetailLoading(true);
    setProfileDetail(null);
    try {
      const { data } = await adminApi.getUserProfile(userId);
      setProfileDetail(data.data);
    } catch {
      setProfileDetailOpen(false);
      toast.add('Failed to load profile', 'error');
    } finally {
      setProfileDetailLoading(false);
    }
  };

  const closeUserProfile = () => {
    setProfileDetailOpen(false);
    setProfileDetail(null);
  };

  const handleVerify = async (userId, verified) => {
    try {
      const res = verified ? await adminApi.verifySupplierPost(userId) : await adminApi.unverifySupplier(userId);
      const score = res.data.data?.score;
      const u = res.data.data?.user;
      setSuppliers((prev) =>
        prev.map((s) => {
          const id = s._id || s.id;
          if (id !== userId) return s;
          return {
            ...s,
            isVerifiedSupplier: u?.isVerifiedSupplier ?? verified,
            trustScore: score?.total_score ?? s.trustScore,
            trustLevel: score?.trust_level ?? s.trustLevel,
          };
        })
      );
      if (profileDetail?.user) {
        const pid = profileDetail.user._id || profileDetail.user.id;
        if (String(pid) === String(userId)) {
          setProfileDetail((d) =>
            d
              ? {
                  ...d,
                  user: { ...d.user, ...u },
                  score: score || d.score,
                }
              : d
          );
        }
      }
      toast.add(
        verified ? 'Supplier verified and trust score recalculated' : 'Supplier unverified and trust score recalculated',
        'success'
      );
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
                Buyers, supplier verification, catalog, RFQs, orders, and immutable activity logs—high-impact actions are visually separated.
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
          <div className="px-5 py-3 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center gap-3 bg-white/80">
            <div className="relative flex-1 min-w-0 max-w-lg">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
              <Input
                className="!pl-9"
                value={supplierSearch}
                onChange={(e) => setSupplierSearch(e.target.value)}
                placeholder="Search name, email, company, GST, location, phone, trust…"
                aria-label="Search suppliers"
              />
            </div>
            <p className="text-xs text-slate-500 shrink-0">
              {filteredSuppliers.length} of {suppliers.length} shown
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="text-left p-4 font-semibold">Name</th>
                  <th className="text-left p-4 font-semibold">Email</th>
                  <th className="text-left p-4 font-semibold">GST</th>
                  <th className="text-left p-4 font-semibold">Company</th>
                  <th className="text-left p-4 font-semibold">Location</th>
                  <th className="text-left p-4 font-semibold">Phone</th>
                  <th className="text-left p-4 font-semibold">Website</th>
                  <th className="text-left p-4 font-semibold">Trust score</th>
                  <th className="text-left p-4 font-semibold">Verified</th>
                  <th className="text-left p-4 font-semibold">Status</th>
                  <th className="text-left p-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredSuppliers.length === 0 && (
                  <tr>
                    <td colSpan={11} className="p-8 text-center text-slate-500 text-sm">
                      {suppliers.length === 0 ? 'No suppliers.' : 'No suppliers match your search.'}
                    </td>
                  </tr>
                )}
                {filteredSuppliers.map((u) => {
                  const uid = u._id || u.id;
                  return (
                    <tr key={uid} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-4 font-medium text-slate-900 max-w-[10rem]">
                        <button
                          type="button"
                          onClick={() => void openUserProfile(String(uid))}
                          className="text-left w-full text-teal-800 hover:text-teal-600 hover:underline"
                        >
                          {u.name}
                        </button>
                      </td>
                      <td className="p-4 text-slate-600">{u.email}</td>
                      <td className="p-4 text-slate-600 font-mono text-xs">{u.gstNumber || '—'}</td>
                      <td className="p-4 text-slate-600 max-w-[14rem]">
                        <div className="font-medium text-slate-800">{u.companyName || '—'}</div>
                        {u.description ? <div className="text-xs text-slate-500 mt-1 line-clamp-2">{u.description}</div> : null}
                      </td>
                      <td className="p-4 text-slate-600 text-xs">
                        {[u.city, u.state, u.country].filter(Boolean).join(' · ') || '—'}
                      </td>
                      <td className="p-4 text-slate-600 text-xs whitespace-nowrap">{u.phone || '—'}</td>
                      <td className="p-4 text-slate-600 text-xs max-w-[10rem] truncate" title={u.website || ''}>
                        {u.website ? (
                          <a href={u.website.startsWith('http') ? u.website : `https://${u.website}`} className="text-teal-700 hover:underline" target="_blank" rel="noreferrer">
                            {u.website}
                          </a>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="p-4 tabular-nums text-slate-800">
                        {u.trustScore != null ? `${Math.round(u.trustScore)}` : '—'}
                        {u.trustLevel && <span className="text-slate-400 text-xs ml-1">({u.trustLevel})</span>}
                      </td>
                      <td className="p-4">{u.isVerifiedSupplier ? <Badge variant="success">Verified</Badge> : <Badge variant="warning">Pending</Badge>}</td>
                      <td className="p-4">
                        {u.isBanned ? <Badge variant="danger">Banned</Badge> : <span className="text-slate-500 text-xs">Active</span>}
                      </td>
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
                          {u.isBanned ? (
                            <Button size="sm" variant="secondary" className="rounded-lg" onClick={() => handleBan(String(uid), false)}>
                              Unban user
                            </Button>
                          ) : (
                            <Button size="sm" variant="outlineDanger" className="rounded-lg" onClick={() => handleBan(String(uid), true)}>
                              Ban user
                            </Button>
                          )}
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
            <p className="section-title">Buyers</p>
          </div>
          <div className="px-5 py-3 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center gap-3 bg-white/80">
            <div className="relative flex-1 min-w-0 max-w-lg">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
              <Input
                className="!pl-9"
                value={buyerSearch}
                onChange={(e) => setBuyerSearch(e.target.value)}
                placeholder="Search by name, email, or id…"
                aria-label="Search buyers"
              />
            </div>
            <p className="text-xs text-slate-500 shrink-0">
              {filteredBuyers.length} of {users.length} shown
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="text-left p-4 font-semibold">Name</th>
                  <th className="text-left p-4 font-semibold">Email</th>
                  <th className="text-left p-4 font-semibold">Status</th>
                  <th className="text-left p-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredBuyers.length === 0 && (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-slate-500 text-sm">
                      {users.length === 0 ? 'No buyers.' : 'No buyers match your search.'}
                    </td>
                  </tr>
                )}
                {filteredBuyers.map((u) => (
                  <tr key={u._id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-4 font-medium text-slate-900 max-w-[12rem]">
                        <button
                          type="button"
                          onClick={() => void openUserProfile(String(u._id))}
                          className="text-left w-full text-teal-800 hover:text-teal-600 hover:underline"
                        >
                          {u.name}
                        </button>
                    </td>
                    <td className="p-4 text-slate-600">{u.email}</td>
                    <td className="p-4">
                      {u.isBanned && <Badge variant="danger">Banned</Badge>}
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

      {tab === 'billing' && (
        <div className="space-y-6">
          {revenue && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card className="p-4 border-emerald-100">
                <p className="text-xs font-semibold text-slate-500 uppercase">Subscription revenue (INR, demo)</p>
                <p className="text-2xl font-bold text-emerald-700">₹{revenue.subscription_revenue_inr}</p>
              </Card>
              <Card className="p-4 border-sky-100">
                <p className="text-xs font-semibold text-slate-500 uppercase">Escrow volume (INR, demo)</p>
                <p className="text-2xl font-bold text-sky-700">₹{revenue.escrow_payment_volume_inr}</p>
              </Card>
              <Card className="p-4">
                <p className="text-xs font-semibold text-slate-500">Successful / failed</p>
                <p className="text-lg font-bold text-slate-800">
                  {revenue.successful_payments} / {revenue.failed_payments}
                </p>
              </Card>
              <Card className="p-4">
                <p className="text-xs font-semibold text-slate-500">Sellers: GO / PRO / free</p>
                <p className="text-sm text-slate-800">
                  {revenue.sellers_by_plan_go} GO, {revenue.sellers_by_plan_pro} PRO, {revenue.sellers_by_plan_free} free
                </p>
              </Card>
              <Card className="p-4">
                <p className="text-xs font-semibold text-slate-500">Active subs (rows)</p>
                <p className="text-sm">
                  GO {revenue.active_go_sellers} · PRO {revenue.active_pro_sellers}
                </p>
              </Card>
            </div>
          )}
          <Card>
            <div className="px-4 py-3 border-b border-slate-100">
              <h2 className="section-title">Seller subscriptions (demo)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500">
                    <th className="p-2">Seller</th>
                    <th className="p-2">Plan</th>
                    <th className="p-2">Status</th>
                    <th className="p-2">Started</th>
                    <th className="p-2">Expires</th>
                  </tr>
                </thead>
                <tbody>
                  {subscriptions.slice(0, 200).map((s) => (
                    <tr key={s._id} className="border-b border-slate-50">
                      <td className="p-2">{s.sellerEmail || s.sellerName || '—'}</td>
                      <td className="p-2 capitalize">{s.plan}</td>
                      <td className="p-2">{s.status}</td>
                      <td className="p-2 text-xs">{s.startedAt ? formatDateTimeIst(s.startedAt) : '—'}</td>
                      <td className="p-2 text-xs">{s.expiresAt ? formatDateTimeIst(s.expiresAt) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <Card>
            <div className="px-4 py-3 border-b border-slate-100">
              <h2 className="section-title">Payments (demo)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500">
                    <th className="p-2">Id</th>
                    <th className="p-2">User</th>
                    <th className="p-2">Type</th>
                    <th className="p-2">₹</th>
                    <th className="p-2">Status</th>
                    <th className="p-2">Method</th>
                    <th className="p-2">When</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.slice(0, 200).map((p) => (
                    <tr key={p._id} className="border-b border-slate-50">
                      <td className="p-2 font-mono text-xs">{(p._id || p.id || '').toString().slice(-8)}</td>
                      <td className="p-2">{p.userEmail || p.userName || '—'}</td>
                      <td className="p-2">{p.paymentType}</td>
                      <td className="p-2">{p.amount}</td>
                      <td className="p-2">{p.status}</td>
                      <td className="p-2">{p.method || '—'}</td>
                      <td className="p-2 text-xs">{p.createdAt ? formatDateTimeIst(p.createdAt) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}


      {tab === 'moderation' && (
        <Card>
          <div className="px-5 py-4 border-b border-slate-100">
            <h2 className="section-title">RFQ chat moderation</h2>
            <p className="text-sm text-slate-500 mt-1">
              Flagged and scored messages: raw text, display text, detection types, and scores for review.
            </p>
          </div>
          <div className="p-4 overflow-x-auto">
            {!flaggedMessages?.length ? (
              <p className="text-sm text-slate-500">No moderated messages</p>
            ) : (
              <table className="w-full text-sm text-left min-w-[56rem]">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                    <th className="py-2 pr-3">RFQ</th>
                    <th className="py-2 pr-3">Sender</th>
                    <th className="py-2 pr-3">Role</th>
                    <th className="py-2 pr-3">Score</th>
                    <th className="py-2 pr-3">Types</th>
                    <th className="py-2 pr-3">Reasons</th>
                    <th className="py-2 pr-3">Preview</th>
                    <th className="py-2">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {flaggedMessages.map((row, i) => {
                    const reasons = Array.isArray(row.moderationReasons)
                      ? row.moderationReasons.join('; ')
                      : row.moderationReason || '';
                    const types = row.detectedTypes || [];
                    return (
                    <tr key={row.messageId || i} className="border-b border-slate-50 align-top">
                      <td className="py-2 pr-3 font-mono text-xs whitespace-nowrap">
                        {row.rfqId ? <Link to={`/rfq/${row.rfqId}`} className="text-teal-700 hover:underline">{String(row.rfqId).slice(-8)}</Link> : '—'}
                      </td>
                      <td className="py-2 pr-3 text-slate-700">{row.sender?.name || row.sender?.email || '—'}</td>
                      <td className="py-2 pr-3">{row.senderRole || '—'}</td>
                      <td className="py-2 pr-3 tabular-nums font-medium">{row.moderationScore ?? '—'}</td>
                      <td className="py-2 pr-3">
                        <div className="flex flex-wrap gap-1">
                          {types.includes('PHONE') && <Badge variant="danger" className="text-[10px]">PHONE</Badge>}
                          {types.includes('EMAIL') && <Badge variant="warning" className="text-[10px]">EMAIL</Badge>}
                          {types.includes('CONTACT_PHRASE') && <Badge variant="outline" className="text-[10px]">PHRASE</Badge>}
                          {!types.length && <span className="text-slate-400">—</span>}
                        </div>
                      </td>
                      <td className="py-2 pr-3 text-slate-600 max-w-xs text-xs">{reasons ? reasons.slice(0, 160) : '—'}</td>
                      <td className="py-2 pr-3 text-slate-500 max-w-md text-xs" title={row.rawMessage || row.displayMessage}>
                        {(row.displayMessage || row.rawMessage || '—').slice(0, 120)}
                      </td>
                      <td className="py-2 text-slate-500 text-xs whitespace-nowrap">
                        {row.createdAt ? (typeof row.createdAt === 'string' ? row.createdAt : formatDateTimeIst(row.createdAt)) : '—'}
                      </td>
                    </tr>
                  );
                  })}
                </tbody>
              </table>
            )}
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
                    <td className="p-4 text-slate-500 whitespace-nowrap align-top text-xs tabular-nums">{log.createdAt ? formatDateTimeIst(log.createdAt) : '—'}</td>
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

      {profileDetailOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
            <div className="flex items-start justify-between gap-2 mb-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Account details</h3>
                <p className="text-sm text-slate-500">Admin read-only view</p>
              </div>
              <Button type="button" variant="ghost" size="sm" className="shrink-0" onClick={closeUserProfile} aria-label="Close">
                <X className="h-5 w-5" />
              </Button>
            </div>
            {profileDetailLoading && <p className="text-slate-500 text-sm">Loading…</p>}
            {!profileDetailLoading && profileDetail?.user && (
              <div className="space-y-4 text-sm">
                <div className="grid sm:grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase text-slate-500">Name</p>
                    <p className="text-slate-900 font-medium">{profileDetail.user.name}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase text-slate-500">Email</p>
                    <p className="text-slate-900 break-all">{profileDetail.user.email}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase text-slate-500">Role</p>
                    <p className="text-slate-900 capitalize">{profileDetail.user.role}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase text-slate-500">Status</p>
                    <p className="text-slate-900">
                      {profileDetail.user.isBanned ? <Badge variant="danger">Banned</Badge> : 'Active'}
                    </p>
                  </div>
                </div>
                {profileDetail.company && (
                  <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
                    <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Company</p>
                    <dl className="grid sm:grid-cols-2 gap-2 text-slate-800">
                      <div><dt className="text-slate-500">Name</dt><dd>{profileDetail.company.companyName || '—'}</dd></div>
                      <div><dt className="text-slate-500">GST</dt><dd className="font-mono text-xs">{profileDetail.company.gstNumber || '—'}</dd></div>
                      <div><dt className="text-slate-500">Phone</dt><dd>{profileDetail.company.phone || '—'}</dd></div>
                      <div><dt className="text-slate-500">Location</dt><dd>{[profileDetail.company.city, profileDetail.company.state, profileDetail.company.country].filter(Boolean).join(' · ') || '—'}</dd></div>
                      {profileDetail.company.description && (
                        <div className="sm:col-span-2"><dt className="text-slate-500">Description</dt><dd className="mt-1 text-slate-600">{profileDetail.company.description}</dd></div>
                      )}
                    </dl>
                  </div>
                )}
                {profileDetail.user.role === 'seller' && (
                  <div className="border border-teal-100 rounded-xl p-4 bg-teal-50/30">
                    <p className="text-xs font-semibold uppercase text-teal-800 mb-2">Trust score</p>
                    {profileDetail.score ? (
                      <div className="space-y-2">
                        <p>
                          <span className="font-bold text-2xl tabular-nums text-teal-800">{Math.round(profileDetail.score.total_score ?? 0)}</span>
                          <span className="text-slate-500 ml-2">/ 100</span>
                          {profileDetail.score.trust_level && (
                            <Badge className="ml-2" variant="teal">{profileDetail.score.trust_level}</Badge>
                          )}
                        </p>
                        {profileDetail.score.verified_status != null && (
                          <p className="text-xs text-slate-600">
                            Verified component: {Number(profileDetail.score.verified_status)}% (15% of total)
                          </p>
                        )}
                        <dl className="grid sm:grid-cols-2 gap-2 text-xs text-slate-700 mt-2">
                          <div>Profile completeness <span className="font-mono">{(profileDetail.score.profile_completeness ?? 0).toFixed(1)}</span></div>
                          <div>Response rate (model) <span className="font-mono">{(profileDetail.score.response_rate ?? 0).toFixed(1)}</span></div>
                          <div>Product strength <span className="font-mono">{(profileDetail.score.product_strength ?? 0).toFixed(1)}</span></div>
                          <div>Buyer rating <span className="font-mono">{(profileDetail.score.buyer_rating ?? 0).toFixed(1)}</span></div>
                        </dl>
                      </div>
                    ) : (
                      <p className="text-slate-500">No score document yet. Use Recalculate score.</p>
                    )}
                    <Link
                      to={`/suppliers/${profileDetail.user._id || profileDetail.user.id}`}
                      className="inline-flex items-center gap-1 text-teal-700 font-semibold text-sm mt-3 hover:underline"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Public supplier page <ExternalLink className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}
