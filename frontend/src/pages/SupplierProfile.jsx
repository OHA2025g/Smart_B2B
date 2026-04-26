import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, MapPin, Package, FileText, CheckCircle, Clock, Award, BarChart3 } from 'lucide-react';
import { suppliersApi, productsApi } from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { getCategoryImage } from '../utils/getCategoryImage';

function MetricTile({ label, value, sub }) {
  return (
    <div className="rounded-2xl border border-slate-200/90 bg-gradient-to-b from-white to-slate-50/80 p-5 shadow-sm hover:shadow-md transition-shadow">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900 tabular-nums">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function SupplierProfile() {
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    suppliersApi
      .getProfile(id)
      .then((r) => setProfile(r.data.data?.profile || null))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    productsApi.list().then((r) => {
      const list = r.data.data?.products || [];
      setProducts(list.filter((p) => (p.seller?.id || p.seller?._id || p.seller)?.toString() === id));
    }).catch(() => setProducts([]));
  }, [id]);

  const displayProducts = (profile?.recent_products?.length ? profile.recent_products : products) || [];

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl">
        <div className="h-48 rounded-3xl bg-slate-200 animate-pulse" />
        <div className="h-8 w-64 bg-slate-200 rounded-xl animate-pulse" />
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="h-32 bg-slate-100 rounded-2xl animate-pulse" />
          <div className="h-32 bg-slate-100 rounded-2xl animate-pulse" />
        </div>
      </div>
    );
  }
  if (!profile) {
    return (
      <Card>
        <EmptyState
          title="Supplier not found"
          description="This supplier profile is unavailable or was removed."
          action={<Link to="/products"><span className="text-teal-600 font-semibold">Browse products</span></Link>}
        />
      </Card>
    );
  }

  const seller = profile.seller || {};
  const company = profile.company || {};
  const trustScore = Math.min(100, Number(profile.trust_score ?? 0));
  const trustLevel = profile.trust_level || 'Low Trust';
  const displayName = company.companyName || seller.name || profile.seller_name || 'Supplier';
  const initial = displayName.slice(0, 1).toUpperCase();

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 max-w-5xl">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-3xl bg-slate-900 text-white shadow-2xl shadow-slate-900/20 ring-1 ring-white/10">
        <div className="absolute inset-0 bg-mesh-dark bg-mesh opacity-90" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl -translate-y-1/3 translate-x-1/3" />
        <div className="relative px-6 sm:px-10 py-10 sm:py-12">
          <div className="flex flex-col sm:flex-row sm:items-end gap-6 sm:justify-between">
            <div className="flex items-start gap-5">
              <div className="h-20 w-20 sm:h-24 sm:w-24 rounded-2xl bg-gradient-to-br from-teal-400 to-teal-700 flex items-center justify-center text-3xl font-black shadow-xl shadow-teal-900/40 ring-2 ring-white/20 shrink-0">
                {initial}
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{displayName}</h1>
                  {profile.verified && (
                    <Badge variant="success" className="gap-1 font-semibold !bg-emerald-500/20 !text-emerald-100 !ring-emerald-400/40">
                      <CheckCircle className="h-3.5 w-3.5" /> Verified supplier
                    </Badge>
                  )}
                </div>
                <p className="text-slate-300 text-sm">{profile.seller_name || seller.name}</p>
                {profile.email && <p className="text-slate-400 text-xs mt-1">{profile.email}</p>}
                {profile.city && (
                  <p className="text-slate-300 mt-3 flex items-center gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-teal-300 shrink-0" /> {profile.city}
                  </p>
                )}
              </div>
            </div>
            <div className="flex flex-wrap gap-2 sm:justify-end">
              <span className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-sm font-medium backdrop-blur-sm ring-1 ring-white/15">
                <Award className="h-4 w-4 text-amber-300" />
                {trustLevel}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        <Card className="lg:col-span-2 border-slate-200/90 shadow-lg shadow-slate-200/40 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-teal-50/80 to-white">
            <h2 className="section-title flex items-center gap-2">
              <Shield className="h-5 w-5 text-teal-600" /> Trust profile
            </h2>
            <p className="text-sm text-slate-500 mt-1">Signals buyers see when evaluating quotes.</p>
          </div>
          <div className="p-6 space-y-6">
            <div>
              <div className="flex justify-between text-sm font-semibold text-slate-700 mb-2">
                <span>Trust score</span>
                <span className="tabular-nums text-teal-700">{Math.round(trustScore)} / 100</span>
              </div>
              <div className="h-4 rounded-full bg-slate-100 overflow-hidden ring-1 ring-slate-200/80 shadow-inner">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${trustScore}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  className="h-full rounded-full bg-gradient-to-r from-teal-500 via-emerald-500 to-teal-400 shadow-sm"
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 mt-1.5 uppercase tracking-wider font-medium">
                <span>Developing</span>
                <span>Marketplace standard</span>
                <span>Elite</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="teal" className="font-semibold">
                {trustLevel}
              </Badge>
              {profile.verified && (
                <Badge variant="success" className="font-semibold gap-1">
                  <CheckCircle className="h-3 w-3" /> Platform verified
                </Badge>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-slate-50 border border-slate-100 p-4 text-center">
                <p className="text-2xl font-bold text-teal-600 tabular-nums">{Math.round(trustScore)}</p>
                <p className="text-xs text-slate-500 mt-1 font-medium">Score</p>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-100 p-4 text-center">
                <p className="text-lg font-bold text-slate-800 leading-tight">{profile.response_rate ?? 0}%</p>
                <p className="text-xs text-slate-500 mt-1 font-medium">Response rate</p>
              </div>
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-3 border-slate-200/90 shadow-lg shadow-slate-200/40">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-teal-600" />
            <div>
              <h2 className="section-title">Performance metrics</h2>
              <p className="text-sm text-slate-500">Operational footprint on SmartB2B.</p>
            </div>
          </div>
          <div className="p-5 sm:p-6 grid grid-cols-2 sm:grid-cols-3 gap-4">
            <MetricTile label="Active products" value={profile.total_products ?? profile.active_products ?? 0} />
            <MetricTile label="RFQs received" value={profile.rfqs_received ?? profile.total_rfqs_received ?? 0} />
            <MetricTile label="Quotes sent" value={profile.quotes_submitted ?? profile.total_quotes_submitted ?? 0} />
            <MetricTile
              label="Quote win rate"
              value={profile.quote_acceptance_rate != null ? `${profile.quote_acceptance_rate}%` : '—'}
            />
            <MetricTile label="Orders fulfilled" value={profile.orders_fulfilled ?? profile.total_orders_fulfilled ?? 0} />
            <MetricTile
              label="Avg. response"
              value={profile.average_response_time_hours != null ? `${profile.average_response_time_hours}h` : '—'}
              sub="To submit quote"
            />
            <MetricTile label="Avg. rating" value={profile.average_rating ?? '—'} sub="Derived signal" />
          </div>
        </Card>
      </div>

      {profile.categories_served?.length > 0 && (
        <Card className="border-slate-200/90">
          <div className="px-5 py-4 border-b border-slate-100">
            <h2 className="section-title">Categories served</h2>
          </div>
          <div className="p-5 flex flex-wrap gap-2">
            {profile.categories_served.map((c) => (
              <Badge key={c} variant="teal" className="font-medium px-3 py-1">
                {c}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {company.description && (
        <Card className="border-slate-200/90">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <FileText className="h-5 w-5 text-slate-600" />
            <h2 className="section-title">About</h2>
          </div>
          <div className="p-5 sm:p-6">
            <p className="text-slate-600 leading-relaxed max-w-3xl">{company.description}</p>
          </div>
        </Card>
      )}

      <Card className="border-slate-200/90 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex flex-wrap items-center justify-between gap-2">
          <h2 className="section-title flex items-center gap-2">
            <Package className="h-5 w-5 text-teal-600" /> Recent listings
          </h2>
          <Link to={`/products`} className="text-sm font-semibold text-teal-600 hover:text-teal-700">
            Browse marketplace →
          </Link>
        </div>
        <div className="p-5 sm:p-6">
          {displayProducts.length > 0 ? (
            <div className="grid sm:grid-cols-2 gap-4">
              {displayProducts.slice(0, 8).map((p) => {
                const { gradient } = getCategoryImage(p.category);
                return (
                  <Link key={p.id || p._id} to={`/product/${p.id || p._id}`} className="group">
                    <div className="flex rounded-2xl border border-slate-200 overflow-hidden bg-white shadow-sm hover:shadow-lg hover:border-teal-200 transition-all">
                      <div className={`w-24 shrink-0 bg-gradient-to-br ${gradient} flex items-center justify-center text-white font-bold`}>
                        {(p.title || '?').slice(0, 1)}
                      </div>
                      <div className="p-4 min-w-0 flex-1">
                        <p className="font-semibold text-slate-900 line-clamp-2 group-hover:text-teal-700 transition-colors">{p.title}</p>
                        <p className="text-teal-600 font-bold mt-1">₹{p.price}</p>
                        {p.category && <Badge variant="outline" className="mt-2 text-[10px]">{p.category}</Badge>}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-10">No products listed yet.</p>
          )}
        </div>
      </Card>

      {profile.recent_activity?.length > 0 && (
        <Card className="border-slate-200/90">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <Clock className="h-5 w-5 text-teal-600" />
            <div>
              <h2 className="section-title">Recent activity</h2>
              <p className="text-sm text-slate-500">Latest events tied to this supplier.</p>
            </div>
          </div>
          <ul className="divide-y divide-slate-100">
            {profile.recent_activity.map((ev) => (
              <li key={ev.id || ev._id} className="px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6">
                <span className="text-xs font-medium text-slate-400 tabular-nums shrink-0 sm:w-44">
                  {ev.created_at ? new Date(ev.created_at).toLocaleString() : ''}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-900">{ev.event_label}</p>
                  <Badge variant="outline" className="mt-2 text-[10px]">
                    {ev.actor_role}
                  </Badge>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </motion.div>
  );
}
