import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Shield,
  Zap,
  Users,
  Package,
  CheckCircle,
  Sparkles,
  Quote,
  FileText,
  ChevronRight,
  ShieldCheck,
  FolderKanban,
  MapPin,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { categoriesApi, productsApi, publicApi } from '../api/client';

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
  { step: 1, title: 'Browse Products', desc: 'Search by category, city, and trust signals—save favorites to your wishlist.' },
  { step: 2, title: 'Add to RFQ Cart', desc: 'Curate line items and quantities; one RFQ bundles everything for suppliers.' },
  { step: 3, title: 'Receive Quotes', desc: 'Verified sellers respond with price, delivery, and availability in one thread.' },
  { step: 4, title: 'Compare & Order', desc: 'Ranked quotes surface the best fit; accept to generate an order in-platform.' },
];

export default function Home() {
  const [categories, setCategories] = useState([]);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [verifiedSuppliers, setVerifiedSuppliers] = useState([]);
  const [stats, setStats] = useState([
    { label: 'Products', value: '—', sub: 'Listings' },
    { label: 'Suppliers', value: '—', sub: 'On platform' },
    { label: 'RFQs', value: '—', sub: 'Raised' },
    { label: 'Orders', value: '—', sub: 'Completed' },
  ]);

  useEffect(() => {
    publicApi.marketStats().then((r) => {
      const st = r.data.data?.stats;
      if (!st) return;
      setStats([
        { label: 'Products', value: String(st.totalProducts ?? '—'), sub: 'Listings' },
        { label: 'Suppliers', value: String(st.suppliers ?? '—'), sub: 'On platform' },
        { label: 'RFQs', value: String(st.totalRfqs ?? '—'), sub: 'Raised' },
        { label: 'Orders', value: String(st.totalOrders ?? '—'), sub: 'Completed' },
      ]);
    }).catch(() => {});
    categoriesApi.list().then((r) => {
      const cats = r.data.data?.categories || [];
      setCategories(cats);
    }).catch(() => {});
    productsApi.list().then((r) => {
      const list = r.data.data?.products || [];
      setFeaturedProducts(list.slice(0, 8));
    }).catch(() => {});
    productsApi
      .list({ verified_only: true })
      .then((r) => {
        const list = r.data.data?.products || [];
        const seen = new Set();
        const sellers = [];
        for (const p of list) {
          const sid = (p.seller?._id || p.seller?.id)?.toString();
          if (!sid || seen.has(sid)) continue;
          seen.add(sid);
          sellers.push({ ...p.seller, _id: sid, sampleCity: p.city });
          if (sellers.length >= 6) break;
        }
        setVerifiedSuppliers(sellers);
      })
      .catch(() => setVerifiedSuppliers([]));
  }, []);

  return (
    <div className="min-h-screen">
      {/* Dark hero - contained so layout stays on screen */}
      <section className="relative min-h-[88vh] flex flex-col justify-center overflow-hidden bg-slate-900 rounded-3xl ring-1 ring-white/10 shadow-2xl shadow-slate-900/20">
        <div className="absolute inset-0 bg-mesh-dark bg-mesh bg-[length:200%_200%] animate-gradient-shift" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-slate-900/30 pointer-events-none" />
        <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-[0.07]" />
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
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.07] border border-white/15 text-slate-200 text-sm font-medium mb-8 backdrop-blur-md shadow-inner-glow"
          >
            <Sparkles className="h-4 w-4 text-teal-400" />
            Procurement-focused B2B marketplace
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 max-w-4xl mx-auto leading-[1.08]"
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
            className="text-lg sm:text-xl text-slate-300/90 mb-4 max-w-2xl mx-auto text-balance leading-relaxed"
          >
            <span className="text-white font-semibold">B2Bभारत</span> connects buyers and verified suppliers for structured sourcing:
            catalog discovery, RFQ carts, ranked quote comparison, and order handoff—built for teams who buy at scale.
          </motion.p>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.3 }}
            className="text-sm sm:text-base text-slate-500 mb-12 max-w-xl mx-auto"
          >
            Trust scores, verification badges, and quote scoring help you decide faster—with audit-friendly activity on every RFQ.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
            className="flex flex-col items-center gap-6"
          >
            <div className="flex flex-wrap gap-3 sm:gap-4 justify-center w-full max-w-3xl">
              <Link to="/products">
                <Button
                  size="lg"
                  className="gap-2 bg-coral-500 text-white hover:bg-coral-600 border-0 shadow-glow-coral hover:shadow-[0_0_50px_-12px_rgba(244,63,94,0.5)] transition-all duration-300 rounded-2xl px-8 py-4 text-base font-semibold group min-w-[200px] justify-center"
                >
                  Browse Products
                  <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link to="/cart">
                <Button
                  size="lg"
                  className="gap-2 bg-teal-500 text-white hover:bg-teal-600 border-0 shadow-lg shadow-teal-900/30 rounded-2xl px-8 py-4 text-base font-semibold min-w-[200px] justify-center"
                >
                  <FileText className="h-5 w-5" /> RFQ Cart
                </Button>
              </Link>
            </div>
            <div className="flex flex-wrap gap-2 sm:gap-3 justify-center items-center text-sm">
              <Link to="/products?verified_only=true">
                <Button
                  size="lg"
                  variant="secondary"
                  className="gap-2 !bg-white/10 !text-white !border-white/20 hover:!bg-white/15 backdrop-blur-sm rounded-xl px-5 py-3"
                >
                  <ShieldCheck className="h-4 w-4 text-teal-300" /> Verified suppliers
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="secondary" size="lg" className="gap-2 !bg-white/5 !text-white !border-white/10 rounded-xl px-5 py-3">
                  Sign up free
                </Button>
              </Link>
            </div>
            <Link to="/login" className="text-slate-400 hover:text-teal-300 transition-colors text-sm font-medium">
              Already have an account? Log in →
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
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
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
          className="max-w-6xl mx-auto px-4 sm:px-6 py-20"
        >
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-10">
            <div>
              <p className="section-heading mb-2">Catalog</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Featured categories</h2>
              <p className="text-slate-500 mt-2 max-w-xl">Jump into high-intent sourcing lanes—each category opens a filtered product view.</p>
            </div>
            <Link to="/products" className="text-teal-600 font-semibold text-sm inline-flex items-center gap-1 hover:gap-2 transition-all shrink-0">
              View all <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {categories.slice(0, 10).map((c) => (
              <Link key={c.id || c._id} to={`/products?category=${encodeURIComponent(c.name || c.slug || '')}`}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="group h-full rounded-2xl border border-slate-200/90 bg-white p-5 shadow-md shadow-slate-200/40 hover:shadow-xl hover:border-teal-200/80 transition-all duration-300"
                >
                  <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-teal-500 to-teal-700 text-white flex items-center justify-center mb-4 shadow-lg shadow-teal-500/25 group-hover:scale-105 transition-transform">
                    <FolderKanban className="h-5 w-5" />
                  </div>
                  <p className="font-semibold text-slate-900 group-hover:text-teal-700 transition-colors">{c.name}</p>
                  <p className="text-xs text-slate-400 mt-1">Browse listings</p>
                </motion.div>
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
        className="max-w-6xl mx-auto px-4 sm:px-6 py-20"
      >
        <div className="text-center max-w-2xl mx-auto mb-12">
          <p className="section-heading mb-2">Workflow</p>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">How it works</h2>
          <p className="text-slate-500 mt-3">From catalog to contract-ready order in four clear steps.</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-4">
          {howItWorks.map((h) => (
            <div key={h.step} className="relative">
              <div className="h-full bg-white rounded-2xl border border-slate-200/90 p-6 shadow-md shadow-slate-200/30 hover:shadow-lg hover:border-teal-200/70 transition-all">
                <div className="w-11 h-11 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center text-sm shadow-md shadow-teal-600/30 mb-4">
                  {h.step}
                </div>
                <h3 className="font-bold text-slate-900 text-lg">{h.title}</h3>
                <p className="text-sm text-slate-500 mt-2 leading-relaxed">{h.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.section>

      {/* Verified suppliers spotlight */}
      {verifiedSuppliers.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-6xl mx-auto px-4 sm:px-6 pb-8"
        >
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-10">
            <div>
              <p className="section-heading mb-2">Trust</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Verified suppliers</h2>
              <p className="text-slate-500 mt-2 max-w-xl">Platform-verified sellers with visible trust scores—start sourcing with confidence.</p>
            </div>
            <Link to="/products?verified_only=true" className="text-teal-600 font-semibold text-sm inline-flex items-center gap-1 hover:gap-2 transition-all">
              See all verified <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {verifiedSuppliers.map((s) => (
              <Link key={s._id} to={`/suppliers/${s._id}`}>
                <motion.div
                  whileHover={{ y: -3 }}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-md shadow-slate-200/40 hover:shadow-xl hover:border-teal-200 transition-all h-full flex flex-col"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="h-12 w-12 rounded-xl bg-slate-900 text-white font-bold flex items-center justify-center shrink-0 text-lg">
                        {(s.name || '?').slice(0, 1).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-slate-900 truncate">{s.name}</p>
                        {s.city || s.sampleCity ? (
                          <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                            <MapPin className="h-3 w-3 shrink-0" />
                            {s.city || s.sampleCity}
                          </p>
                        ) : null}
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold px-2.5 py-1 ring-1 ring-emerald-200/80 shrink-0">
                      <CheckCircle className="h-3.5 w-3.5" /> Verified
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs">
                    {s.trustLevel && (
                      <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium">{s.trustLevel}</span>
                    )}
                    {s.trustScore != null && (
                      <span className="px-2.5 py-1 rounded-full bg-teal-50 text-teal-800 font-medium">
                        Trust {Math.round(s.trustScore)}%
                      </span>
                    )}
                  </div>
                </motion.div>
              </Link>
            ))}
          </div>
        </motion.section>
      )}

      {/* Featured products */}
      {featuredProducts.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-6xl mx-auto px-4 sm:px-6 py-16"
        >
          <div className="flex items-end justify-between gap-4 mb-8">
            <div>
              <p className="section-heading mb-2">Spotlight</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Featured products</h2>
            </div>
            <Link to="/products" className="text-teal-600 font-semibold text-sm hidden sm:inline-flex items-center gap-1">
              View catalog <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {featuredProducts.map((p) => (
              <Link key={p.id || p._id} to={`/product/${p.id || p._id}`}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="bg-white rounded-2xl border border-slate-200/90 overflow-hidden shadow-md shadow-slate-200/40 hover:shadow-xl hover:border-teal-200 transition-all group h-full flex flex-col"
                >
                  <div className="h-28 bg-gradient-to-br from-teal-500 via-teal-600 to-slate-800 relative">
                    <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-20" />
                    <span className="absolute bottom-3 left-3 text-white/90 text-xs font-semibold uppercase tracking-wide">
                      {p.category || 'Product'}
                    </span>
                  </div>
                  <div className="p-4 flex-1 flex flex-col">
                    <p className="font-semibold text-slate-900 line-clamp-2 text-sm group-hover:text-teal-700 transition-colors">{p.title}</p>
                    <p className="text-teal-600 font-bold mt-2">₹{p.price}</p>
                  </div>
                </motion.div>
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
            Why B2Bभारत?
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
          {features.map((f) => (
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
              “B2Bभारत cut our sourcing time in half. We get verified quotes in days, not weeks.”
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
              Join buyers and suppliers who use B2Bभारत to discover products and close deals.
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
              <span className="font-semibold text-slate-800">B2Bभारत</span>
            </div>
            <div className="flex gap-6 text-sm text-slate-600">
              <Link to="/products" className="hover:text-teal-600">Products</Link>
              <Link to="/" className="hover:text-teal-600">How it works</Link>
              <Link to="/register" className="hover:text-teal-600">Sign up</Link>
              <Link to="/login" className="hover:text-teal-600">Log in</Link>
            </div>
          </div>
          <p className="text-slate-500 text-sm mt-6">© B2Bभारत — Intelligent B2B Marketplace. Find trusted suppliers, raise RFQs, compare quotes.</p>
        </div>
      </footer>
    </div>
  );
}
