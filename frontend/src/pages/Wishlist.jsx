import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Heart, Trash2, ShoppingCart } from 'lucide-react';
import { wishlistApi, cartApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { getCategoryImage } from '../utils/getCategoryImage';

export default function Wishlist() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchItems = async () => {
    try {
      const { data } = await wishlistApi.get();
      setItems(data.data.items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleRemove = async (productId) => {
    try {
      await wishlistApi.remove(productId);
      setItems((prev) => prev.filter((i) => i.productId?._id !== productId));
      toast.add('Removed from wishlist', 'success');
    } catch {
      toast.add('Failed to remove', 'error');
    }
  };

  const handleAddToCart = async (productId) => {
    try {
      await cartApi.add({ productId, quantity: 1 });
      toast.add('Added to RFQ cart', 'success');
    } catch {
      toast.add('Failed to add to cart', 'error');
    }
  };

  if (loading) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;
  if (!items.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Wishlist</h1>
        <Card>
          <EmptyState
            icon={Heart}
            title="Your wishlist is empty"
            description="Save products you like from the Products page."
            action={<Link to="/products"><Button>Browse products</Button></Link>}
          />
        </Card>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-2xl font-bold mb-6">Wishlist</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => {
          const p = item.productId;
          if (!p) return null;
          const { gradient } = getCategoryImage(p.category);
          return (
            <Card key={item._id} className="flex flex-col">
              <div className={`h-32 bg-gradient-to-br ${gradient} flex items-center justify-center text-white font-bold`}>
                {p.category?.slice(0, 2) || '—'}
              </div>
              <div className="p-4 flex-1">
                <Link to={`/product/${p._id}`} className="font-medium text-neutral-900 hover:text-primary-600 line-clamp-2">
                  {p.title}
                </Link>
                <p className="text-sm text-primary-600 mt-1">₹{p.price} / {p.unit}</p>
              </div>
              <div className="p-4 border-t flex gap-2">
                <Button size="sm" variant="secondary" className="gap-1" onClick={() => handleAddToCart(p._id)}>
                  <ShoppingCart className="h-4 w-4" /> Add to cart
                </Button>
                <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleRemove(p._id)}>
                  <Trash2 className="h-4 w-4" /> Remove
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
