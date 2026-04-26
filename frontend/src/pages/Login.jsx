import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingBag, ArrowRight, Shield, Zap, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

const benefits = [
  { icon: Zap, text: 'Quick access to suppliers and buyers' },
  { icon: Shield, text: 'Verified B2B marketplace' },
  { icon: Users, text: 'Connect with businesses across categories' },
];

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await authApi.login({ email, password });
      login(data.data.user, data.data.token);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.response?.data?.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-[70vh] flex items-center justify-center"
    >
      <div className="w-full max-w-5xl flex flex-col lg:flex-row rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
        {/* Left: Brand panel */}
        <div className="lg:w-2/5 relative bg-gradient-to-br from-slate-900 via-teal-900/95 to-slate-900 text-white p-8 lg:p-12 flex flex-col justify-center overflow-hidden">
          <div
            className="absolute inset-0 bg-cover bg-center opacity-20 mix-blend-overlay"
            style={{ backgroundImage: "url('https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&q=60')" }}
          />
          <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-30" />
          <Link to="/" className="relative inline-flex items-center gap-2 text-white/95 hover:text-white mb-8 transition-colors">
            <ShoppingBag className="h-8 w-8" />
            <span className="font-bold text-xl">B2Bभारत</span>
          </Link>
          <h2 className="relative text-2xl font-bold mb-4">Welcome back</h2>
          <p className="relative text-slate-300 mb-8">Sign in to manage your listings and inquiries.</p>
          <ul className="relative space-y-4">
            {benefits.map((b, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * i }}
                className="flex items-center gap-3"
              >
                <b.icon className="h-5 w-5 text-teal-300 shrink-0" />
                <span className="text-sm text-slate-300">{b.text}</span>
              </motion.li>
            ))}
          </ul>
        </div>
        {/* Right: Form */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className="lg:w-3/5 p-8 lg:p-12 flex flex-col justify-center"
        >
          <h3 className="text-2xl font-bold text-slate-900 mb-2">Login</h3>
          <p className="text-slate-500 mb-6">Enter your credentials to continue.</p>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <Button type="submit" disabled={loading} className="w-full gap-2">
              {loading ? 'Signing in...' : 'Sign in'}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>
          <p className="mt-6 text-sm text-neutral-500">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="text-teal-600 font-semibold hover:underline">
              Sign up
            </Link>
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}
