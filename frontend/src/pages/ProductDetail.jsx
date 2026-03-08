import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Minus, Plus, Send, MapPin, Shield, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { productsApi, inquiriesApi } from '../api/client';
import { getCategoryImage } from '../utils/getCategoryImage';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [submitStatus, setSubmitStatus] = useState({ type: '', text: '' });

  useEffect(() => {
    productsApi
      .getById(id)
      .then((res) => setProduct(res.data.data.product))
      .catch(() => setProduct(null))
      .finally(() => setLoading(false));
  }, [id]);

  const handleInquiry = async (e) => {
    e.preventDefault();
    if (!user) {
      navigate('/login');
      return;
    }
    if (user.role !== 'buyer') {
      setSubmitStatus({ type: 'error', text: 'Only buyers can send inquiries.' });
      return;
    }
    setSubmitStatus({ type: '', text: '' });
    try {
      await inquiriesApi.create({ productId: id, message, quantity });
      setSubmitStatus({ type: 'success', text: 'Inquiry sent successfully.' });
      setMessage('');
      setQuantity(product?.minOrderQuantity || 1);
    } catch (err) {
      setSubmitStatus({
        type: 'error',
        text: err.response?.data?.message || 'Failed to send inquiry.',
      });
    }
  };

  const minQty = product?.minOrderQuantity || 1;
  const inc = () => setQuantity((q) => q + 1);
  const dec = () => setQuantity((q) => Math.max(minQty, q - 1));

  if (loading) {
    return (
      <div className="max-w-4xl animate-pulse space-y-6">
        <div className="h-64 bg-neutral-200 rounded-xl" />
        <div className="h-8 bg-neutral-200 rounded w-2/3" />
        <div className="h-4 bg-neutral-200 rounded w-1/2" />
      </div>
    );
  }
  if (!product) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-600">
        Product not found.
      </motion.div>
    );
  }

  const { gradient } = getCategoryImage(product.category);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-5xl"
    >
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Gallery */}
        <div className="space-y-3">
          <div className={`aspect-square rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white text-6xl font-bold`}>
            {product.category?.slice(0, 2) || 'PD'}
          </div>
          <div className="flex gap-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className={`w-20 h-20 rounded-lg bg-gradient-to-br ${gradient} opacity-80`} />
            ))}
          </div>
        </div>

        {/* Info */}
        <div>
          <Badge variant="primary" className="mb-2">{product.category}</Badge>
          <h1 className="text-2xl font-bold text-neutral-900">{product.title}</h1>
          <p className="mt-2 text-3xl font-semibold text-primary-600">
            ₹{product.price} <span className="text-lg font-normal text-neutral-500">/ {product.unit}</span>
          </p>
          <p className="mt-4 text-neutral-600">{product.description || 'No description.'}</p>
          <ul className="mt-4 space-y-1 text-sm text-neutral-500">
            <li>Min order: {product.minOrderQuantity ?? 1}</li>
            {product.city && (
              <li className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {product.city}
              </li>
            )}
          </ul>
          {product.seller && (
            <p className="mt-2 text-sm text-neutral-500">Seller: {product.seller.name}</p>
          )}
        </div>
      </div>

      {/* Supplier card (placeholder) */}
      <Card className="mt-8">
        <CardHeader className="flex flex-row items-center justify-between">
          <span className="font-medium">Supplier info</span>
          <Badge variant="success">Verified</Badge>
        </CardHeader>
        <CardBody className="grid sm:grid-cols-3 gap-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-primary-100 p-2">
              <Shield className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-xs text-neutral-500">Trust score</p>
              <p className="font-semibold">78/100</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-primary-100 p-2">
              <Clock className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-xs text-neutral-500">Response time</p>
              <p className="font-semibold">Within 24h</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-emerald-500" />
            <div>
              <p className="text-xs text-neutral-500">Verification</p>
              <p className="font-semibold">Verified</p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Inquiry form */}
      {user?.role === 'buyer' && (
        <Card className="mt-8">
          <div className="p-6">
            <h2 className="text-lg font-medium mb-4">Send inquiry</h2>
            {submitStatus.text && (
              <div
                className={`mb-4 p-3 rounded-lg ${
                  submitStatus.type === 'success' ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-700'
                }`}
              >
                {submitStatus.text}
              </div>
            )}
            <form onSubmit={handleInquiry} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">Quantity</label>
                <div className="flex items-center gap-2">
                  <Button type="button" variant="secondary" size="sm" onClick={dec} disabled={quantity <= minQty}>
                    <Minus className="h-4 w-4" />
                  </Button>
                  <input
                    type="number"
                    min={minQty}
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value) || minQty)}
                    className="w-24 border border-neutral-300 rounded-lg px-3 py-2 text-center"
                  />
                  <Button type="button" variant="secondary" size="sm" onClick={inc}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">Message</label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  required
                  rows={3}
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                />
              </div>
              <Button type="submit" className="gap-2">
                <Send className="h-4 w-4" />
                Send inquiry
              </Button>
            </form>
          </div>
        </Card>
      )}

      {!user && (
        <p className="mt-6 text-neutral-500">
          <Link to="/login" className="text-primary-600 hover:underline font-medium">Login</Link> as a buyer to send an inquiry.
        </p>
      )}
    </motion.div>
  );
}
