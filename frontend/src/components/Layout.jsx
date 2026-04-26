import { Link, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/" className="text-xl font-semibold text-indigo-600">
            B2Bभारत
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/products" className="text-gray-600 hover:text-indigo-600">
              Products
            </Link>
            {user ? (
              <>
                <Link to="/dashboard" className="text-gray-600 hover:text-indigo-600">
                  Dashboard
                </Link>
                {user.role === 'seller' && (
                  <Link to="/seller/products" className="text-gray-600 hover:text-indigo-600">
                    My Products
                  </Link>
                )}
                {user.role === 'seller' && (
                  <Link to="/profile/company" className="text-gray-600 hover:text-indigo-600">
                    Company
                  </Link>
                )}
                {user.role === 'admin' && (
                  <Link to="/dashboard" className="text-gray-600 hover:text-indigo-600">
                    Admin
                  </Link>
                )}
                <span className="text-gray-500 text-sm">{user.email}</span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-red-600"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-600 hover:text-indigo-600">
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
