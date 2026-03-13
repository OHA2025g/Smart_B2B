import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, MapPin, Package, TrendingUp, FileText, CheckCircle } from 'lucide-react';
import { suppliersApi, productsApi } from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';

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

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-neutral-200 rounded animate-pulse" />
        <div className="h-48 bg-neutral-100 rounded-xl animate-pulse" />
      </div>
    );
  }
  if (!profile) {
    return (
      <EmptyState
        title="Supplier not found"
        description="This supplier profile is unavailable."
        action={<Link to="/products"><span className="text-teal-600 font-medium">Browse products</span></Link>}
      />
    );
  }

  const seller = profile.seller || {};
  const company = profile.company || {};
  const trustScore = profile.trust_score ?? 0;
  const trustLevel = profile.trust_level || 'Low Trust';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            {company.companyName || seller.name || 'Supplier'}
            {profile.verified && (
              <Badge variant="success" className="gap-1">
                <CheckCircle className="h-4 w-4" /> Verified Supplier
              </Badge>
            )}
          </h1>
          {profile.city && (
            <p className="text-slate-500 mt-1 flex items-center gap-1">
              <MapPin className="h-4 w-4" /> {profile.city}
            </p>
          )}
        </div>
      </div>

      <Card>
        <div className="p-6">
          <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-teal-600" /> Trust & activity
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-2xl font-bold text-teal-600">{trustScore}</p>
              <p className="text-sm text-slate-500">Trust score</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-slate-700">{trustLevel}</p>
              <p className="text-sm text-slate-500">Trust level</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-700">{profile.response_rate ?? 0}%</p>
              <p className="text-sm text-slate-500">Response rate</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-700">{profile.average_rating ?? '—'}</p>
              <p className="text-sm text-slate-500">Avg. rating</p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-teal-600" /> Metrics
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div><p className="text-xl font-semibold">{profile.total_products ?? 0}</p><p className="text-sm text-slate-500">Products</p></div>
            <div><p className="text-xl font-semibold">{profile.rfqs_received ?? 0}</p><p className="text-sm text-slate-500">RFQs received</p></div>
            <div><p className="text-xl font-semibold">{profile.quotes_submitted ?? 0}</p><p className="text-sm text-slate-500">Quotes submitted</p></div>
            <div><p className="text-xl font-semibold">{profile.orders_fulfilled ?? 0}</p><p className="text-sm text-slate-500">Orders fulfilled</p></div>
          </div>
        </div>
      </Card>

      {profile.categories_served?.length > 0 && (
        <Card>
          <div className="p-6">
            <h2 className="font-semibold text-slate-900 mb-3">Categories served</h2>
            <div className="flex flex-wrap gap-2">
              {profile.categories_served.map((c) => (
                <Badge key={c} variant="default">{c}</Badge>
              ))}
            </div>
          </div>
        </Card>
      )}

      {company.description && (
        <Card>
          <div className="p-6">
            <h2 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
              <FileText className="h-5 w-5" /> About
            </h2>
            <p className="text-slate-600">{company.description}</p>
          </div>
        </Card>
      )}

      <Card>
        <div className="p-6">
          <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Package className="h-5 w-5 text-teal-600" /> Products by this supplier
          </h2>
          {products.length > 0 ? (
            <ul className="space-y-2">
              {products.slice(0, 20).map((p) => (
                <li key={p.id || p._id}>
                  <Link to={`/product/${p.id || p._id}`} className="flex justify-between py-2 border-b border-slate-100 last:border-0 hover:text-teal-600">
                    <span className="font-medium">{p.title}</span>
                    <span className="text-teal-600">₹{p.price}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500 text-sm">No products listed yet.</p>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
