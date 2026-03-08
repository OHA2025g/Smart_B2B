import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ProtectedRoute } from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import SellerProducts from './pages/SellerProducts';
import SellerRFQs from './pages/SellerRFQs';
import SellerOrders from './pages/SellerOrders';
import CompanyProfile from './pages/CompanyProfile';
import Wishlist from './pages/Wishlist';
import Cart from './pages/Cart';
import RFQList from './pages/RFQList';
import RFQDetail from './pages/RFQDetail';
import AdminPanel from './pages/AdminPanel';
import Home from './pages/Home';

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="products" element={<Products />} />
        <Route path="product/:id" element={<ProductDetail />} />
        <Route path="wishlist" element={<ProtectedRoute allowedRoles={['buyer']}><Wishlist /></ProtectedRoute>} />
        <Route path="cart" element={<ProtectedRoute allowedRoles={['buyer']}><Cart /></ProtectedRoute>} />
        <Route path="rfq" element={<ProtectedRoute allowedRoles={['buyer']}><RFQList /></ProtectedRoute>} />
        <Route path="rfq/:id" element={<ProtectedRoute><RFQDetail /></ProtectedRoute>} />
        <Route path="seller/rfqs" element={<ProtectedRoute allowedRoles={['seller']}><SellerRFQs /></ProtectedRoute>} />
        <Route path="seller/orders" element={<ProtectedRoute allowedRoles={['seller']}><SellerOrders /></ProtectedRoute>} />
        <Route path="admin/panel" element={<ProtectedRoute allowedRoles={['admin']}><AdminPanel /></ProtectedRoute>} />
        <Route
          path="dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="seller/products"
          element={
            <ProtectedRoute allowedRoles={['seller']}>
              <SellerProducts />
            </ProtectedRoute>
          }
        />
        <Route
          path="profile/company"
          element={
            <ProtectedRoute allowedRoles={['seller']}>
              <CompanyProfile />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
