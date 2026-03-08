import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Filter, Package, Heart, ShoppingCart } from 'lucide-react';
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

export default function Products() {
  const { user } = useAuth();
  const toast = useToast();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [wishlistIds, setWishlistIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [city, setCity] = useState('');

  useEffect(() => {
    categoriesApi.list().then((res) => setCategories(res.data.data.categories || [])).catch(() => {});
  }, []);
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
    try {
      const params = {};
      if (srch) params.search = srch;
      if (cat) params.category = cat;
      if (cty) params.city = cty;
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
  }, []);

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

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl bg-slate-900 text-white px-6 py-12 sm:py-14 mb-8 shadow-xl"
      >
        <div className="absolute inset-0 bg-mesh-dark bg-mesh opacity-90" />
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative flex flex-col sm:flex-row sm:items-center gap-6">
          <div className="hidden sm:flex h-16 w-16 rounded-2xl bg-teal-500/30 items-center justify-center shrink-0">
            <Package className="h-9 w-9 text-teal-200" />
          </div>
          <div className="flex-1">
            <h1 className="text-3xl sm:text-4xl font-extrabold mb-1">Find products</h1>
            <p className="text-slate-400">Search by category, location or keyword</p>
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

      {/* Filters */}
      <form onSubmit={handleFilter} className="flex flex-wrap items-end gap-3 mb-8">
        <div className="w-48">
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="w-40">
          <Input
            placeholder="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </div>
        <div className="w-40">
          <Input
            placeholder="City"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />
        </div>
        <Button type="submit" className="gap-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white border-0">
          <Filter className="h-4 w-4" />
          Filter
        </Button>
      </form>

      {/* List */}
      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : products.length === 0 ? (
        <Card>
          <EmptyState
            icon={Package}
            title="No products found"
            description="Try adjusting your filters or search term."
            action={<Button onClick={fetchProducts}>Clear filters</Button>}
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
                  <Card hover className="h-full flex flex-col relative group">
                    {user?.role === 'buyer' && (
                      <button
                        type="button"
                        onClick={(e) => handleWishlist(e, p._id)}
                        className="absolute top-2 right-2 z-10 p-1.5 rounded-full bg-white/90 shadow text-red-500 hover:bg-white"
                      >
                        <Heart className={`h-5 w-5 ${wishlistIds.has(p._id) ? 'fill-current' : ''}`} />
                      </button>
                    )}
                    <Link to={`/product/${p._id}`} className="flex flex-col flex-1 relative group">
                      <div className={`h-44 bg-gradient-to-br ${gradient} flex items-center justify-center text-white text-2xl font-bold relative overflow-hidden`}>
                        <span className="relative z-10">{label.slice(0, 2)}</span>
                        <div className="absolute inset-0 bg-slate-900/0 group-hover:bg-slate-900/40 transition-colors duration-300" />
                      </div>
                      <div className="p-4 flex-1 flex flex-col">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-bold text-slate-900 line-clamp-2">{p.title}</h3>
                          <Badge className="bg-teal-100 text-teal-700 border-0">{p.category}</Badge>
                        </div>
                        {p.city && (
                          <p className="mt-1 text-xs text-neutral-500 flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {p.city}
                          </p>
                        )}
                        <p className="mt-2 text-teal-600 font-bold">
                          ₹{p.price} <span className="text-neutral-500 font-normal text-sm">/ {p.unit}</span>
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-neutral-500">
                          <span>MOQ: {p.minOrderQuantity ?? 1}</span>
                          <span>·</span>
                          <span>Delivery: —</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2 items-center">
                          {p.seller?.isVerifiedSupplier && <Badge variant="success">Verified Supplier</Badge>}
                          {p.seller?.trustScore != null && (
                            <span className="text-xs text-neutral-600" title={`Trust level: ${p.seller?.trustLevel || ''}`}>
                              Trust {Math.round(p.seller.trustScore)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </Link>
                    {user?.role === 'buyer' && (
                      <div className="p-4 border-t" onClick={(e) => e.stopPropagation()}>
                        <Button size="sm" className="w-full gap-2 bg-teal-600 hover:bg-teal-700 text-white border-0" onClick={(e) => handleAddToCart(e, p._id, p.minOrderQuantity || 1)}>
                          <ShoppingCart className="h-4 w-4" /> Add to RFQ Cart
                        </Button>
                      </div>
                    )}
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
