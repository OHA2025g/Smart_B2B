import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingBag, ArrowRight, Shield, Zap, Users, Package, CheckCircle, Sparkles, Quote, FileText } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { categoriesApi, productsApi } from '../api/client';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.15 },
  },
};

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0 },
};

const features = [
  { icon: Shield, title: 'Verified suppliers', desc: 'Trust scores & verified badges on every listing', color: 'from-teal-500 to-emerald-600', bg: 'bg-teal-500/10' },
  { icon: Zap, title: 'Quick RFQ flow', desc: 'Request quotes, compare offers, order in one place', color: 'from-amber-500 to-orange-500', bg: 'bg-amber-500/10' },
  { icon: Users, title: 'B2B network', desc: 'Connect with buyers and sellers across industries', color: 'from-rose-500 to-pink-500', bg: 'bg-rose-500/10' },
];

const howItWorks = [
  { step: 1, title: 'Browse', desc: 'Explore products and add to wishlist or RFQ cart' },
  { step: 2, title: 'Add to RFQ cart', desc: 'Build your request for quote from cart or product pages' },
  { step: 3, title: 'Receive quotes', desc: 'Suppliers submit quotes; compare price, delivery & trust' },
  { step: 4, title: 'Compare & order', desc: 'Accept the best quote and place your order' },
];

export default function Home() {
  const [categories, setCategories] = useState([]);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [stats, setStats] = useState([
    { label: 'Categories', value: '—', sub: 'Industries' },
    { label: 'Suppliers', value: '—', sub: 'Trusted' },
    { label: 'Products', value: '—', sub: 'Listings' },
  ]);

  useEffect(() => {
    categoriesApi.list().then((r) => {
      const cats = r.data.data?.categories || [];
      setCategories(cats);
      setStats((s) => [{ ...s[0], value: String(cats.length) }, s[1], s[2]]);
    }).catch(() => {});
    productsApi.list().then((r) => {
      const list = r.data.data?.products || [];
      setFeaturedProducts(list.slice(0, 8));
      const total = list.length;
      setStats((s) => [s[0], s[1], { ...s[2], value: String(total) }]);
    }).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen">
      {/* Dark hero - contained so layout stays on screen */}
      <section className="relative min-h-[85vh] flex flex-col justify-center overflow-hidden bg-slate-900 rounded-3xl">
        <div className="absolute inset-0 bg-mesh-dark bg-mesh bg-[length:200%_200%] animate-gradient-shift" />
        <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-[0.06]" />
        {/* Floating blobs */}
        <motion.div
          className="absolute top-1/4 left-1/4 w-72 h-72 rounded-full bg-teal-500/20 blur-3xl"
          animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-rose-500/15 blur-3xl"
          animate={{ x: [0, -25, 0], y: [0, 15, 0] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute top-1/2 right-1/3 w-48 h-48 rounded-full bg-amber-500/10 blur-2xl"
          animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 6, repeat: Infinity }}
        />

        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-24 sm:py-32 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-slate-300 text-sm font-medium mb-8 backdrop-blur-sm"
          >
            <Sparkles className="h-4 w-4 text-teal-400" />
            Trusted B2B marketplace
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 max-w-4xl mx-auto leading-[1.1]"
          >
            Find Trusted Suppliers.{' '}
            <span className="bg-gradient-to-r from-teal-400 via-teal-300 to-cyan-300 bg-clip-text text-transparent">
              Raise RFQs. Compare Quotes. Procure Better.
            </span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.25 }}
            className="text-lg sm:text-xl text-slate-400 mb-12 max-w-2xl mx-auto"
          >
            B2B marketplace with verified suppliers, RFQ flow, and quote comparison—all in one place.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
            className="flex flex-wrap gap-4 justify-center"
          >
            <Link to="/products">
              <Button
                size="lg"
                className="gap-2 bg-coral-500 text-white hover:bg-coral-600 border-0 shadow-glow-coral hover:shadow-[0_0_50px_-12px_rgba(244,63,94,0.5)] transition-all duration-300 rounded-2xl px-8 py-4 text-base font-semibold group"
              >
                Browse Products
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/cart">
              <Button
                size="lg"
                className="gap-2 bg-white/10 text-white border border-white/20 hover:bg-white/15 backdrop-blur-sm rounded-2xl px-8 py-4"
              >
                <FileText className="h-5 w-5" /> Create RFQ
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="secondary" size="lg" className="gap-2 bg-white/5 text-white border border-white/10 rounded-2xl px-8 py-4">
                Sign up free
              </Button>
            </Link>
            <Link to="/login">
              <span className="text-slate-400 hover:text-white transition-colors font-medium cursor-pointer inline-block mt-2">
                Already have an account? Log in →
              </span>
            </Link>
          </motion.div>
        </div>
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-slate-500 text-sm">
          Scroll to explore
        </div>
      </section>

      {/* Stats strip */}
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="relative z-10 max-w-5xl mx-auto px-4 -mt-16 sm:-mt-20"
      >
        <div className="grid grid-cols-3 gap-4">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -4 }}
              className="bg-white rounded-2xl border border-slate-200/80 shadow-xl shadow-slate-200/50 p-6 sm:p-8 text-center"
            >
              <p className="text-2xl sm:text-4xl font-extrabold text-teal-600">{s.value}</p>
              <p className="text-sm font-medium text-slate-700 mt-1">{s.label}</p>
              <p className="text-xs text-slate-400">{s.sub}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Featured categories */}
      {categories.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-6xl mx-auto px-4 sm:px-6 py-16"
        >
          <h2 className="text-2xl font-bold text-slate-900 mb-6">Featured categories</h2>
          <div className="flex flex-wrap gap-3">
            {categories.slice(0, 10).map((c) => (
              <Link key={c.id || c._id} to={`/products?category=${encodeURIComponent(c.name || c.slug || '')}`}>
                <span className="inline-block px-4 py-2 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 hover:bg-teal-100 font-medium">
                  {c.name}
                </span>
              </Link>
            ))}
          </div>
        </motion.section>
      )}

      {/* How it works */}
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-6xl mx-auto px-4 sm:px-6 py-16"
      >
        <h2 className="text-2xl font-bold text-slate-900 mb-8">How it works</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {howItWorks.map((h, i) => (
            <div key={h.step} className="relative bg-white rounded-2xl border border-slate-200 p-6">
              <div className="w-10 h-10 rounded-full bg-teal-100 text-teal-700 font-bold flex items-center justify-center mb-3">{h.step}</div>
              <h3 className="font-semibold text-slate-900">{h.title}</h3>
              <p className="text-sm text-slate-500 mt-1">{h.desc}</p>
              {i < howItWorks.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-0.5 bg-slate-200" />
              )}
            </div>
          ))}
        </div>
      </motion.section>

      {/* Featured products */}
      {featuredProducts.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-6xl mx-auto px-4 sm:px-6 py-16"
        >
          <h2 className="text-2xl font-bold text-slate-900 mb-6">Featured products</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {featuredProducts.map((p) => (
              <Link key={p.id || p._id} to={`/product/${p.id || p._id}`}>
                <div className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-lg hover:border-teal-200 transition-all">
                  <p className="font-medium text-slate-900 truncate">{p.title}</p>
                  <p className="text-teal-600 font-semibold mt-1">₹{p.price}</p>
                  {p.category && <span className="text-xs text-slate-400">{p.category}</span>}
                </div>
              </Link>
            ))}
          </div>
          <div className="mt-6 text-center">
            <Link to="/products">
              <Button variant="secondary" className="rounded-xl">View all products</Button>
            </Link>
          </div>
        </motion.section>
      )}

      {/* Bento-style features */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-24">
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <motion.h2 variants={item} className="text-3xl sm:text-4xl font-extrabold text-slate-900 mb-3">
            Why SmartB2B?
          </motion.h2>
          <motion.p variants={item} className="text-slate-500 text-lg max-w-xl mx-auto">
            Everything you need to source and sell—with trust built in.
          </motion.p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid sm:grid-cols-3 gap-6"
        >
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              variants={item}
              whileHover={{ y: -6, transition: { duration: 0.2 } }}
              className="group relative bg-white rounded-3xl border border-slate-200 shadow-lg shadow-slate-200/30 overflow-hidden hover:shadow-card-hover hover:border-teal-200 transition-all duration-300"
            >
              <div className={`absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r ${f.color}`} />
              <div className="p-8">
                <div className={`inline-flex p-4 rounded-2xl ${f.bg} text-teal-600 group-hover:scale-110 transition-transform duration-300`}>
                  <f.icon className="h-7 w-7" />
                </div>
                <h3 className="font-bold text-slate-900 text-xl mt-5 mb-2">{f.title}</h3>
                <p className="text-slate-500">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Social proof / quote block */}
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-4xl mx-auto px-4 sm:px-6 py-16"
      >
        <div className="relative rounded-3xl bg-slate-900 text-white p-10 sm:p-14 overflow-hidden">
          <div className="absolute inset-0 bg-mesh-dark opacity-80" />
          <div className="absolute top-0 right-0 w-64 h-64 bg-teal-500/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
          <Quote className="absolute top-8 left-8 h-12 w-12 text-white/10" />
          <div className="relative">
            <p className="text-xl sm:text-2xl font-medium text-slate-200 leading-relaxed mb-6">
              “SmartB2B cut our sourcing time in half. We get verified quotes in days, not weeks.”
            </p>
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center text-lg font-bold">
                A
              </div>
              <div>
                <p className="font-semibold text-white">Procurement lead</p>
                <p className="text-slate-400 text-sm">Manufacturing company</p>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      {/* CTA */}
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-4xl mx-auto px-4 sm:px-6 py-24"
      >
        <div className="relative rounded-3xl bg-gradient-to-br from-teal-600 to-teal-700 p-12 sm:p-16 text-center overflow-hidden">
          <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-10" />
          <div className="relative">
            <Package className="h-14 w-14 mx-auto mb-6 text-white/80 animate-float" />
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-3">Ready to grow your business?</h2>
            <p className="text-teal-100 text-lg mb-10 max-w-md mx-auto">
              Join buyers and suppliers who use SmartB2B to discover products and close deals.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Link to="/register">
                <Button size="lg" className="gap-2 bg-coral-500 text-white hover:bg-coral-600 border-0 rounded-2xl px-8 py-4 shadow-glow-coral font-semibold group">
                  Get started free
                  <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link to="/products">
                <Button variant="secondary" size="lg" className="bg-white/15 text-white border-white/30 hover:bg-white/25 rounded-2xl px-8 py-4">
                  Browse products
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-50 mt-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Package className="h-6 w-6 text-teal-600" />
              <span className="font-semibold text-slate-800">SmartB2B</span>
            </div>
            <div className="flex gap-6 text-sm text-slate-600">
              <Link to="/products" className="hover:text-teal-600">Products</Link>
              <Link to="/" className="hover:text-teal-600">How it works</Link>
              <Link to="/register" className="hover:text-teal-600">Sign up</Link>
              <Link to="/login" className="hover:text-teal-600">Log in</Link>
            </div>
          </div>
          <p className="text-slate-500 text-sm mt-6">© SmartB2B — Intelligent B2B Marketplace. Find trusted suppliers, raise RFQs, compare quotes.</p>
        </div>
      </footer>
    </div>
  );
}
