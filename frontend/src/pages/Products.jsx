import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Filter, Package, Heart, ShoppingCart, ShieldCheck, TrendingUp, Sparkles } from 'lucide-react';
import { productsApi, categoriesApi, wishlistApi, cartApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { SkeletonCard } from '../components/ui/SkeletonCard';
import { EmptyState } from '../components/ui/EmptyState';
import { getCategoryImage } from '../utils/getCategoryImage';

const TRUST_LEVELS = ['Highly Trusted', 'Trusted', 'Moderate', 'Low Trust'];

export default function Products() {
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [wishlistIds, setWishlistIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [city, setCity] = useState('');
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [trustLevel, setTrustLevel] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);

  useEffect(() => {
    categoriesApi.list().then((res) => setCategories(res.data.data.categories || [])).catch(() => {});
  }, []);
  useEffect(() => {
    setVerifiedOnly(searchParams.get('verified_only') === 'true');
  }, [searchParams]);
  useEffect(() => {
    if (user?.role === 'buyer') {
      wishlistApi.get().then((res) => {
        const ids = new Set((res.data.data.items || []).map((i) => i.productId?._id).filter(Boolean));
        setWishlistIds(ids);
      }).catch(() => {});
    }
  }, [user?.role]);

  const fetchProducts = async (overrides = {}) => {
    setLoading(true);
    const cat = overrides.category !== undefined ? overrides.category : category;
    const srch = overrides.search !== undefined ? overrides.search : search;
    const cty = overrides.city !== undefined ? overrides.city : city;
    const vo = overrides.verified_only !== undefined ? overrides.verified_only : verifiedOnly;
    const tl = overrides.trust_level !== undefined ? overrides.trust_level : trustLevel;
    const minP = overrides.min_price !== undefined ? overrides.min_price : minPrice;
    const maxP = overrides.max_price !== undefined ? overrides.max_price : maxPrice;
    try {
      const params = {};
      if (srch) params.search = srch;
      if (cat) params.category = cat;
      if (cty) params.city = cty;
      if (vo) params.verified_only = true;
      if (tl) params.trust_level = tl;
      if (minP !== '' && minP != null) params.min_price = Number(minP);
      if (maxP !== '' && maxP != null) params.max_price = Number(maxP);
      const { data } = await productsApi.list(params);
      setProducts(data.data.products || []);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [verifiedOnly]);

  const handleFilter = (e) => {
    e.preventDefault();
    fetchProducts();
  };

  const handleCategoryChip = (catName) => {
    setCategory(catName);
    fetchProducts({ category: catName });
  };

  const handleWishlist = async (e, productId) => {
    e.preventDefault();
    e.stopPropagation();
    if (user?.role !== 'buyer') return;
    try {
      await wishlistApi.toggle(productId);
      setWishlistIds((prev) => {
        const next = new Set(prev);
        if (next.has(productId)) next.delete(productId);
        else next.add(productId);
        return next;
      });
    } catch {
      toast.add('Failed to update wishlist', 'error');
    }
  };

  const handleAddToCart = async (e, productId, minQty) => {
    e.preventDefault();
    e.stopPropagation();
    if (user?.role !== 'buyer') return;
    try {
      await cartApi.add({ productId, quantity: minQty || 1 });
      toast.add('Added to RFQ cart', 'success');
    } catch {
      toast.add('Failed to add to cart', 'error');
    }
  };

  const resetFilters = () => {
    setSearch('');
    setCategory('');
    setCity('');
    setVerifiedOnly(false);
    setTrustLevel('');
    setMinPrice('');
    setMaxPrice('');
    setLoading(true);
    productsApi
      .list({})
      .then(({ data }) => setProducts(data.data.products || []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  };

  const handleWishlistClick = (e, productId) => {
    e.preventDefault();
    e.stopPropagation();
    if (user?.role !== 'buyer') {
      toast.add('Sign in as a buyer to use the wishlist', 'error');
      return;
    }
    handleWishlist(e, productId);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl bg-slate-900 text-white px-6 py-12 sm:py-14 mb-8 shadow-2xl shadow-slate-900/15 ring-1 ring-white/10"
      >
        <div className="absolute inset-0 bg-mesh-dark bg-mesh opacity-90" />
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative flex flex-col sm:flex-row sm:items-center gap-6">
          <div className="hidden sm:flex h-16 w-16 rounded-2xl bg-teal-500/30 items-center justify-center shrink-0 ring-1 ring-white/20">
            <Package className="h-9 w-9 text-teal-200" />
          </div>
          <div className="flex-1">
            <p className="text-teal-300/90 text-xs font-semibold uppercase tracking-wider mb-2">Marketplace catalog</p>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">Find products</h1>
            <p className="text-slate-400 max-w-xl leading-relaxed">
              Every card shows supplier, location, trust signals, and quick actions—build your RFQ cart as you browse.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Category chips */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            type="button"
            onClick={() => handleCategoryChip('')}
            className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${!category ? 'bg-teal-600 text-white shadow-lg shadow-teal-500/25' : 'bg-white border border-slate-200 text-slate-600 hover:border-teal-300 hover:text-teal-600 hover:shadow-md'}`}
          >
            All
          </button>
          {categories.map((c) => (
            <button
              key={c._id}
              type="button"
              onClick={() => handleCategoryChip(c.name)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${category === c.name ? 'bg-teal-600 text-white shadow-lg shadow-teal-500/25' : 'bg-white border border-slate-200 text-slate-600 hover:border-teal-300 hover:text-teal-600 hover:shadow-md'}`}
            >
              {c.name}
            </button>
          ))}
        </div>
      )}

      <div className="md:hidden mb-4">
        <Button type="button" variant="secondary" className="w-full" onClick={() => setFiltersOpen((o) => !o)}>
          <Filter className="h-4 w-4 mr-2" />
          {filtersOpen ? 'Hide filters' : 'Show filters'}
        </Button>
      </div>
      {/* Filters */}
      <Card className={`mb-8 border-slate-200/90 shadow-lg shadow-slate-200/50 ${filtersOpen ? 'block' : 'hidden'} md:block`}>
        <form onSubmit={handleFilter} className="p-4 sm:p-5 flex flex-col gap-5">
          <div className="flex items-center gap-2 text-slate-700">
            <Filter className="h-4 w-4 text-teal-600" />
            <span className="text-sm font-semibold">Refine results</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4 items-end">
            <div className="min-w-0">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">Search</label>
              <Input placeholder="Keyword…" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <div className="min-w-0">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">Category</label>
              <Input placeholder="Category" value={category} onChange={(e) => setCategory(e.target.value)} />
            </div>
            <div className="min-w-0">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">City</label>
              <Input placeholder="City" value={city} onChange={(e) => setCity(e.target.value)} />
            </div>
            <div className="min-w-0">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">Min ₹</label>
              <Input type="number" placeholder="Min" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} />
            </div>
            <div className="min-w-0">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">Max ₹</label>
              <Input type="number" placeholder="Max" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />
            </div>
            <div className="min-w-0">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">Trust level</label>
              <select
                value={trustLevel}
                onChange={(e) => setTrustLevel(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm bg-white text-slate-800 shadow-sm focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400"
              >
                <option value="">Any</option>
                {TRUST_LEVELS.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4 pt-1 border-t border-slate-100">
            <label className="inline-flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer select-none rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2.5 hover:bg-slate-50">
              <input
                type="checkbox"
                checked={verifiedOnly}
                onChange={(e) => setVerifiedOnly(e.target.checked)}
                className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              />
              <ShieldCheck className="h-4 w-4 text-teal-600 shrink-0" />
              Verified suppliers only
            </label>
            <div className="flex flex-wrap gap-2 sm:ml-auto">
              <Button type="submit" className="gap-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white border-0 shadow-md shadow-teal-600/20">
                <Sparkles className="h-4 w-4" />
                Apply filters
              </Button>
            </div>
          </div>
        </form>
      </Card>

      {/* List */}
      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : products.length === 0 ? (
        <Card className="border-dashed border-slate-200">
          <EmptyState
            icon={Package}
            title="No products match"
            description="Broaden your search, clear price bounds, or turn off “verified only” to see more listings."
            action={
              <Button type="button" variant="secondary" className="rounded-xl" onClick={resetFilters}>
                Reset all filters
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {products.map((p, i) => {
              const { gradient, label } = getCategoryImage(p.category);
              return (
                <motion.div
                  key={p._id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card
                    hover
                    className="h-full flex flex-col relative group transition-shadow duration-300 hover:shadow-2xl hover:shadow-teal-900/5 hover:border-teal-200/90 overflow-visible"
                  >
                    <button
                      type="button"
                      title={user?.role === 'buyer' ? (wishlistIds.has(p._id) ? 'Remove from wishlist' : 'Add to wishlist') : 'Sign in as buyer to save'}
                      onClick={(e) => handleWishlistClick(e, p._id)}
                      className="absolute top-3 right-3 z-20 p-2 rounded-full bg-white/95 shadow-md shadow-slate-300/50 ring-1 ring-slate-200/80 text-rose-500 hover:bg-white hover:scale-105 transition-all"
                    >
                      <Heart className={`h-5 w-5 ${wishlistIds.has(p._id) ? 'fill-current' : ''}`} />
                    </button>
                    <div className="flex flex-col flex-1 relative group min-h-0">
                      <Link to={`/product/${p._id}`} className="flex flex-col flex-1 relative min-h-0">
                        <div
                          className={`h-48 bg-gradient-to-br ${gradient} flex flex-col items-center justify-center text-white relative overflow-hidden ring-1 ring-inset ring-white/20`}
                        >
                          <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-25" />
                          <span className="relative z-10 text-4xl font-black tracking-tight drop-shadow-md">{label.slice(0, 2)}</span>
                          <span className="relative z-10 text-[10px] uppercase tracking-widest text-white/80 mt-2 font-semibold">Listing preview</span>
                          <div className="absolute inset-0 bg-slate-950/0 group-hover:bg-slate-950/25 transition-colors duration-300" />
                          <div className="absolute top-3 left-3 z-10">
                            <Badge variant="teal" className="backdrop-blur-sm bg-white/20 text-white ring-white/30 !text-[10px]">
                              {p.category}
                            </Badge>
                          </div>
                        </div>
                        <div className="p-5 flex-1 flex flex-col gap-3">
                          <h3 className="font-bold text-slate-900 line-clamp-2 text-base leading-snug group-hover:text-teal-700 transition-colors">{p.title}</h3>
                          <div className="flex flex-wrap items-center gap-2">
                            {p.city ? (
                              <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 bg-slate-50 px-2.5 py-1 rounded-lg ring-1 ring-slate-100">
                                <MapPin className="h-3.5 w-3.5 text-teal-600 shrink-0" />
                                {p.city}
                              </span>
                            ) : (
                              <span className="text-xs text-slate-400">Location not set</span>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-2 items-center">
                            {p.seller?.isVerifiedSupplier ? (
                              <Badge variant="success" className="gap-1">
                                <ShieldCheck className="h-3 w-3" /> Verified
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-slate-500">Unverified</Badge>
                            )}
                            {p.seller?.trustScore != null && (
                              <Badge variant="primary" className="gap-1 font-semibold tabular-nums">
                                <TrendingUp className="h-3 w-3" />
                                {Math.round(p.seller.trustScore)}% score
                              </Badge>
                            )}
                            {p.seller?.trustLevel && (
                              <Badge variant="default">{p.seller.trustLevel}</Badge>
                            )}
                          </div>
                          <p className="text-lg font-bold text-teal-600">
                            ₹{p.price}
                            <span className="text-slate-500 font-normal text-sm"> / {p.unit || 'unit'}</span>
                          </p>
                          <p className="text-xs text-slate-400">
                            MOQ {p.minOrderQuantity ?? 1} · Delivery set per quote
                          </p>
                        </div>
                      </Link>
                      <div className="px-5 pb-3 -mt-1">
                        {p.seller?.name ? (
                          <button
                            type="button"
                            onClick={() => navigate(`/suppliers/${p.seller._id || p.seller.id}`)}
                            className="w-full text-left inline-flex items-center gap-2 text-sm text-slate-600 hover:text-teal-700 font-medium rounded-xl hover:bg-slate-50 py-2 -my-1 px-1 transition-colors"
                          >
                            <span className="flex h-7 w-7 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center shrink-0">
                              {p.seller.name.slice(0, 1).toUpperCase()}
                            </span>
                            <span className="truncate">{p.seller.name}</span>
                          </button>
                        ) : (
                          <p className="text-sm text-slate-400">Supplier pending</p>
                        )}
                      </div>
                    </div>
                    <div className="p-4 pt-0 mt-auto" onClick={(e) => e.stopPropagation()}>
                      {user?.role === 'buyer' ? (
                        <Button
                          size="sm"
                          className="w-full gap-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white border-0 shadow-md shadow-teal-600/25 font-semibold"
                          onClick={(e) => handleAddToCart(e, p._id, p.minOrderQuantity || 1)}
                        >
                          <ShoppingCart className="h-4 w-4" /> Add to RFQ Cart
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          className="w-full gap-2 rounded-xl font-semibold border-slate-200"
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            toast.add('Sign in as a buyer to add items to your RFQ cart', 'error');
                          }}
                        >
                          <ShoppingCart className="h-4 w-4" /> Add to RFQ Cart
                        </Button>
                      )}
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
}
