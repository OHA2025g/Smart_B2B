import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingBag, ArrowRight, Shield } from 'lucide-react';
import { Button } from '../components/ui/Button';

export default function Home() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="text-center py-16"
    >
      <h1 className="text-4xl font-bold text-neutral-900 mb-2">SmartB2B</h1>
      <p className="text-neutral-600 mb-10 text-lg">Intelligent B2B Marketplace – Connect with verified suppliers</p>
      <div className="flex gap-4 justify-center flex-wrap">
        <Link to="/products">
          <Button size="lg" className="gap-2">
            <ShoppingBag className="h-5 w-5" />
            Browse Products
          </Button>
        </Link>
        <Link to="/login">
          <Button variant="secondary" size="lg">
            Login
          </Button>
        </Link>
        <Link to="/register">
          <Button variant="secondary" size="lg" className="border-primary-600 text-primary-600 hover:bg-primary-50">
            Sign up
          </Button>
        </Link>
      </div>
    </motion.div>
  );
}
