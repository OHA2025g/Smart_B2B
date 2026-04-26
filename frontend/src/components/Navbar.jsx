import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShoppingBag, LogOut, User, Bell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { notificationsApi } from '../api/client';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === '/';
  const [scrolled, setScrolled] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);

  useEffect(() => {
    if (!user) return;
    notificationsApi.getMe()
      .then((r) => {
        setNotifications(r.data.data?.notifications?.slice(0, 5) || []);
        setUnreadCount(r.data.data?.unreadCount ?? 0);
      })
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const transparent = isHome && !scrolled;
  const navBg = transparent ? 'bg-transparent border-transparent' : 'bg-white/95 backdrop-blur-lg border-slate-200/80 shadow-sm';
  const textStyle = transparent ? 'text-white hover:text-teal-200' : 'text-slate-600 hover:text-teal-600';
  const activeStyle = transparent ? 'text-white' : 'text-teal-600';

  const NavLink = ({ to, children }) => {
    const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
    return (
      <Link
        to={to}
        className={`font-semibold transition-colors relative py-2 ${isActive ? activeStyle : textStyle}`}
      >
        {children}
        {isActive && !transparent && (
          <motion.span
            layoutId="nav-underline"
            className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-500 rounded-full"
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
          />
        )}
      </Link>
    );
  };

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`sticky top-0 z-40 border-b transition-colors duration-300 print:hidden ${navBg}`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 font-bold text-xl transition-opacity hover:opacity-90">
            <ShoppingBag className={`h-7 w-7 shrink-0 ${transparent ? 'text-teal-400' : 'text-teal-600'}`} />
            <span className={transparent ? 'bg-gradient-to-r from-white to-slate-200 bg-clip-text text-transparent' : 'bg-gradient-to-r from-teal-600 to-teal-700 bg-clip-text text-transparent'}>
              SmartB2B
            </span>
          </Link>
          <nav className="flex items-center gap-4 sm:gap-6">
            <NavLink to="/products">Products</NavLink>
            {user ? (
              <>
                {user.role === 'buyer' && (
                  <>
                    <NavLink to="/wishlist">Wishlist</NavLink>
                    <NavLink to="/cart">Cart</NavLink>
                    <NavLink to="/rfq">RFQs</NavLink>
                    <NavLink to="/orders">Orders</NavLink>
                  </>
                )}
                {user.role === 'seller' && (
                  <>
                    <NavLink to="/seller/products">My Products</NavLink>
                    <NavLink to="/seller/rfqs">RFQs</NavLink>
                    <NavLink to="/orders">Orders</NavLink>
                    <NavLink to="/profile/company">Company</NavLink>
                  </>
                )}
                {user.role === 'admin' && (
                  <>
                    <NavLink to="/orders">Orders</NavLink>
                    <NavLink to="/admin/panel">Admin Panel</NavLink>
                  </>
                )}
                <NavLink to="/dashboard">Dashboard</NavLink>
                <div className="relative">
                  <Link
                    to="/notifications"
                    className={`flex items-center gap-1.5 p-2 rounded-lg transition-colors ${transparent ? 'text-slate-300 hover:text-white' : 'text-slate-600 hover:text-teal-600'}`}
                    onMouseEnter={() => setNotifOpen(true)}
                    onMouseLeave={() => setNotifOpen(false)}
                  >
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-coral-500 text-white text-xs flex items-center justify-center">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </span>
                    )}
                  </Link>
                  {notifOpen && (
                    <div
                      className="absolute right-0 top-full mt-1 w-80 bg-white rounded-xl border border-slate-200 shadow-lg py-2 z-50"
                      onMouseEnter={() => setNotifOpen(true)}
                      onMouseLeave={() => setNotifOpen(false)}
                    >
                      <div className="px-3 py-1 border-b border-slate-100 flex justify-between items-center">
                        <span className="font-semibold text-slate-800">Notifications</span>
                        <Link to="/notifications" className="text-sm text-teal-600">View all</Link>
                      </div>
                      {notifications.length === 0 ? (
                        <p className="px-3 py-4 text-slate-500 text-sm">No new notifications</p>
                      ) : (
                        notifications.map((n) => (
                          <Link
                            key={n.id || n._id}
                            to={n.related_entity_type === 'rfq' ? `/rfq/${n.related_entity_id}` : '/notifications'}
                            className="block px-3 py-2 hover:bg-slate-50 text-left"
                          >
                            <p className="font-medium text-slate-800 text-sm truncate">{n.title}</p>
                            <p className="text-xs text-slate-500 truncate">{n.message}</p>
                          </Link>
                        ))
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
                  <span className={`flex items-center gap-1.5 text-sm ${transparent ? 'text-slate-300' : 'text-slate-500'}`}>
                    <User className="h-4 w-4" />
                    {user.email}
                  </span>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className={`flex items-center gap-1.5 text-sm transition-colors ${transparent ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-rose-600'}`}
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <NavLink to="/login">Login</NavLink>
                <Link
                  to="/register"
                  className="bg-coral-500 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-coral-600 hover:shadow-glow-coral transition-all"
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
