import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingBag, LogOut, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navLink = 'text-neutral-600 hover:text-primary-600 font-medium transition-colors';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-neutral-200"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          <Link to="/" className="flex items-center gap-2 text-primary-600 font-bold text-xl">
            <ShoppingBag className="h-6 w-6" />
            SmartB2B
          </Link>
          <nav className="flex items-center gap-4 sm:gap-6">
            <Link to="/products" className={navLink}>
              Products
            </Link>
            {user ? (
              <>
                {user.role === 'buyer' && (
                  <>
                    <Link to="/wishlist" className={navLink}>Wishlist</Link>
                    <Link to="/cart" className={navLink}>Cart</Link>
                    <Link to="/rfq" className={navLink}>RFQs</Link>
                  </>
                )}
                {user.role === 'seller' && (
                  <>
                    <Link to="/seller/products" className={navLink}>My Products</Link>
                    <Link to="/seller/rfqs" className={navLink}>RFQs</Link>
                    <Link to="/seller/orders" className={navLink}>Orders</Link>
                    <Link to="/profile/company" className={navLink}>Company</Link>
                  </>
                )}
                {user.role === 'admin' && (
                  <Link to="/admin/panel" className={navLink}>Admin Panel</Link>
                )}
                <Link to="/dashboard" className={navLink}>Dashboard</Link>
                <div className="flex items-center gap-3 pl-4 border-l border-neutral-200">
                  <span className="flex items-center gap-1.5 text-sm text-neutral-500">
                    <User className="h-4 w-4" />
                    {user.email}
                  </span>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 text-sm text-neutral-600 hover:text-red-600 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link to="/login" className={navLink}>
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-700 transition-colors"
                >
                  Sign up
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </motion.header>
  );
}
