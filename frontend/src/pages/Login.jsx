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
      <div className="w-full max-w-5xl flex flex-col lg:flex-row rounded-2xl border border-neutral-200 bg-white shadow-xl overflow-hidden">
        {/* Left: Brand panel */}
        <div className="lg:w-2/5 bg-gradient-to-br from-primary-600 to-primary-800 text-white p-8 lg:p-12 flex flex-col justify-center">
          <Link to="/" className="inline-flex items-center gap-2 text-white/90 hover:text-white mb-8">
            <ShoppingBag className="h-8 w-8" />
            <span className="font-bold text-xl">SmartB2B</span>
          </Link>
          <h2 className="text-2xl font-bold mb-4">Welcome back</h2>
          <p className="text-primary-100 mb-8">Sign in to manage your listings and inquiries.</p>
          <ul className="space-y-4">
            {benefits.map((b, i) => (
              <li key={i} className="flex items-center gap-3">
                <b.icon className="h-5 w-5 text-primary-200 shrink-0" />
                <span className="text-sm text-primary-100">{b.text}</span>
              </li>
            ))}
          </ul>
        </div>
        {/* Right: Form */}
        <div className="lg:w-3/5 p-8 lg:p-12 flex flex-col justify-center">
          <h3 className="text-2xl font-semibold text-neutral-900 mb-2">Login</h3>
          <p className="text-neutral-500 mb-6">Enter your credentials to continue.</p>
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
            <Link to="/register" className="text-primary-600 font-medium hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </motion.div>
  );
}
