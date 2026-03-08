import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingBag, ArrowRight, Shield, Zap, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

const benefits = [
  { icon: Zap, text: 'List products and receive inquiries' },
  { icon: Shield, text: 'Verified B2B marketplace' },
  { icon: Users, text: 'Connect with buyers and suppliers' },
];

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('buyer');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await authApi.register({ email, password, name, role });
      login(data.data.user, data.data.token);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.response?.data?.message || 'Registration failed.');
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
          <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-30" />
          <Link to="/" className="relative inline-flex items-center gap-2 text-white/95 hover:text-white mb-8 transition-colors">
            <ShoppingBag className="h-8 w-8" />
            <span className="font-bold text-xl">SmartB2B</span>
          </Link>
          <h2 className="relative text-2xl font-bold mb-4">Create an account</h2>
          <p className="relative text-slate-300 mb-8">Join as a buyer or seller to get started.</p>
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
          <h3 className="text-2xl font-semibold text-neutral-900 mb-2">Sign up</h3>
          <p className="text-neutral-500 mb-6">Fill in your details. Password must be at least 6 characters.</p>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input label="Password (min 6)" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">I am a</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setRole('buyer')}
                  className={`flex-1 py-2.5 px-4 rounded-lg border-2 text-sm font-medium transition-colors ${
                    role === 'buyer'
                      ? 'border-teal-600 bg-teal-50 text-teal-700'
                      : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  Buyer
                </button>
                <button
                  type="button"
                  onClick={() => setRole('seller')}
                  className={`flex-1 py-2.5 px-4 rounded-lg border-2 text-sm font-medium transition-colors ${
                    role === 'seller'
                      ? 'border-teal-600 bg-teal-50 text-teal-700'
                      : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  Seller
                </button>
              </div>
            </div>
            <Button type="submit" disabled={loading} className="w-full gap-2">
              {loading ? 'Creating account...' : 'Create account'}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>
          <p className="mt-6 text-sm text-neutral-500">
            Already have an account?{' '}
            <Link to="/login" className="text-teal-600 font-semibold hover:underline">
              Login
            </Link>
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}
