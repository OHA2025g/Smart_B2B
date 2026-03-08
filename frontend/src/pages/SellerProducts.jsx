import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Pencil, Trash2, Eye, LayoutGrid, List } from 'lucide-react';
import { productsApi } from '../api/client';
import { getCategoryImage } from '../utils/getCategoryImage';
import { useToast } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { SkeletonCard } from '../components/ui/SkeletonCard';

export default function SellerProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [addingNew, setAddingNew] = useState(false);
  const [viewMode, setViewMode] = useState('grid');
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: '',
    price: '',
    unit: 'unit',
    minOrderQuantity: 1,
    city: '',
  });
  const [error, setError] = useState('');
  const toast = useToast();

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const { data } = await productsApi.listMy();
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

  const openCreate = () => {
    setEditing(null);
    setAddingNew(true);
    setForm({
      title: '',
      description: '',
      category: '',
      price: '',
      unit: 'unit',
      minOrderQuantity: 1,
      city: '',
    });
    setError('');
  };

  const openEdit = (p) => {
    setEditing(p._id);
    setAddingNew(false);
    setForm({
      title: p.title,
      description: p.description || '',
      category: p.category,
      price: String(p.price),
      unit: p.unit || 'unit',
      minOrderQuantity: p.minOrderQuantity ?? 1,
      city: p.city || '',
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const payload = {
      ...form,
      price: Number(form.price),
      minOrderQuantity: Number(form.minOrderQuantity) || 1,
    };
    try {
      if (editing) {
        await productsApi.update(editing, payload);
        toast.add('Product updated.', 'success');
      } else {
        await productsApi.create(payload);
        toast.add('Product created.', 'success');
        setAddingNew(false);
      }
      setEditing(null);
      fetchProducts();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this product?')) return;
    try {
      await productsApi.delete(id);
      setProducts((prev) => prev.filter((p) => p._id !== id));
      toast.add('Product deleted.', 'success');
    } catch (err) {
      toast.add(err.response?.data?.message || 'Delete failed.', 'error');
    }
  };

  const showForm = editing || addingNew;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold text-neutral-900">Manage Listings</h1>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-neutral-200 p-0.5">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-neutral-500'}`}
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-neutral-500'}`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>
          <Button onClick={openCreate} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Product
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg">{error}</div>
      )}

      {showForm && (
        <Card className="mb-8">
          <div className="p-6">
            <h2 className="text-lg font-medium mb-4">{editing ? 'Edit product' : 'New product'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Title *" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
                <Input label="Category *" value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} required />
                <Input label="Price *" type="number" step="0.01" min="0" value={form.price} onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))} required />
                <Input label="Unit" value={form.unit} onChange={(e) => setForm((f) => ({ ...f, unit: e.target.value }))} />
                <Input label="Min order qty" type="number" min="0" value={form.minOrderQuantity} onChange={(e) => setForm((f) => ({ ...f, minOrderQuantity: e.target.value }))} />
                <Input label="City" value={form.city} onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))} />
              </div>
              <Input label="Description" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
              <div className="flex gap-2">
                <Button type="submit">{editing ? 'Update' : 'Create'}</Button>
                <Button type="button" variant="secondary" onClick={() => { setEditing(null); setAddingNew(false); }}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </Card>
      )}

      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : products.length === 0 ? (
        <Card>
          <EmptyState
            icon={Plus}
            title="No products yet"
            description="Add your first product to start receiving inquiries."
            action={<Button onClick={openCreate}>Add product</Button>}
          />
        </Card>
      ) : viewMode === 'grid' ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence>
            {products.map((p, i) => {
              const { gradient } = getCategoryImage(p.category);
              return (
                <motion.div
                  key={p._id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="overflow-hidden">
                    <div className={`h-32 bg-gradient-to-br ${gradient} flex items-center justify-center text-white font-bold text-xl`}>
                      {p.category?.slice(0, 2) || '—'}
                    </div>
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-semibold text-neutral-900 line-clamp-2">{p.title}</h3>
                        <Badge variant="success">Active</Badge>
                      </div>
                      <p className="text-sm text-neutral-500 mt-1">{p.category} · ₹{p.price}/{p.unit}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Button variant="ghost" size="sm" onClick={() => openEdit(p)} className="gap-1">
                          <Pencil className="h-3.5 w-3.5" />
                          Edit
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(p._id)} className="gap-1 text-red-600 hover:text-red-700">
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </Button>
                        <Link to={`/product/${p._id}`}>
                          <Button variant="ghost" size="sm" className="gap-1">
                            <Eye className="h-3.5 w-3.5" />
                            View
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      ) : (
        <Card>
          <ul className="divide-y divide-neutral-200">
            {products.map((p) => (
              <li key={p._id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4">
                <div>
                  <span className="font-medium text-neutral-900">{p.title}</span>
                  <span className="text-neutral-500 text-sm ml-2">{p.category} · ₹{p.price}/{p.unit}</span>
                </div>
                <div className="flex gap-2">
                  <Badge variant="success">Active</Badge>
                  <Button variant="ghost" size="sm" onClick={() => openEdit(p)}>Edit</Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(p._id)} className="text-red-600">Delete</Button>
                  <Link to={`/product/${p._id}`}><Button variant="ghost" size="sm">View</Button></Link>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </motion.div>
  );
}
