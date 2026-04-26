import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Building2, CheckCircle, Search } from 'lucide-react';
import { suppliersApi } from '../api/client';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';

function trustVariant(level) {
  if (!level) return 'default';
  const s = String(level).toLowerCase();
  if (s.includes('highly')) return 'success';
  if (s.includes('trusted') && !s.includes('low')) return 'primary';
  if (s.includes('moderate')) return 'warning';
  return 'danger';
}

export default function Suppliers() {
  const [list, setList] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [city, setCity] = useState('');
  const [category, setCategory] = useState('');
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [sort, setSort] = useState('trust');

  const params = useMemo(
    () => ({
      search: search.trim() || undefined,
      city: city.trim() || undefined,
      category: category.trim() || undefined,
      verified_only: verifiedOnly || undefined,
      sort,
    }),
    [search, city, category, verifiedOnly, sort],
  );

  useEffect(() => {
    let cancel = false;
    setLoading(true);
    suppliersApi
      .list(params)
      .then((res) => {
        if (cancel) return;
        setList(res.data.data.suppliers || []);
        setTotal(res.data.data.total || 0);
      })
      .catch(() => {
        if (!cancel) {
          setList([]);
          setTotal(0);
        }
      })
      .finally(() => {
        if (!cancel) setLoading(false);
      });
    return () => {
      cancel = true;
    };
  }, [params]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-5xl space-y-6">
      <div>
        <h1 className="page-heading">Suppliers</h1>
        <p className="text-sm text-slate-500 mt-1">
          Discover verified and trusted B2B suppliers. {total ? `Showing ${list.length} of ${total} matches.` : ''}
        </p>
      </div>

      <Card className="p-4 sm:p-5">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-500 uppercase">Search</label>
            <div className="relative mt-1">
              <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Company or name"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase">City</label>
            <Input className="mt-1" value={city} onChange={(e) => setCity(e.target.value)} placeholder="Filter" />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase">Category</label>
            <Input className="mt-1" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Steel" />
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={verifiedOnly}
              onChange={(e) => setVerifiedOnly(e.target.checked)}
            />
            Verified only
          </label>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Sort</span>
            <select
              className="border rounded-lg px-2 py-1.5"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="trust">Trust score</option>
              <option value="orders">Orders</option>
              <option value="products">Products</option>
              <option value="name">Name</option>
            </select>
          </div>
        </div>
      </Card>

      {loading && (
        <div className="h-32 rounded-2xl bg-slate-100 animate-pulse" />
      )}

      {!loading && !list.length && (
        <Card>
          <EmptyState
            icon={Building2}
            title="No suppliers"
            description="Try adjusting filters or search."
          />
        </Card>
      )}

      {!loading && list.length > 0 && (
        <ul className="space-y-3">
          {list.map((s) => (
            <li key={s.sellerId}>
              <Card className="p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="font-semibold text-lg">{s.companyName || s.name || 'Supplier'}</h2>
                      {s.verified && (
                        <Badge variant="success" className="gap-1">
                          <CheckCircle className="h-3 w-3" /> Verified
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-slate-500 mt-1">
                      {s.city || '—'}
                      {typeof s.trustScore === 'number' ? (
                        <>
                          {' '}
                          · Trust {s.trustScore} ·
                          <span className="ml-1">
                            <Badge variant={trustVariant(s.trustLevel)}>{s.trustLevel || '—'}</Badge>
                          </span>
                        </>
                      ) : null}
                    </p>
                    <p className="text-xs text-slate-400 mt-2">
                      {s.productCount} products · {s.orderCount} orders
                    </p>
                  </div>
                  <div className="flex sm:flex-col gap-2 sm:items-end">
                    <Link to={`/suppliers/${s.sellerId}`}>
                      <Button variant="primary">View profile</Button>
                    </Link>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </motion.div>
  );
}
