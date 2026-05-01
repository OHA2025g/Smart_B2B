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
import CompanyProfile from './pages/CompanyProfile';
import Wishlist from './pages/Wishlist';
import Cart from './pages/Cart';
import RFQList from './pages/RFQList';
import RFQDetail from './pages/RFQDetail';
import AdminPanel from './pages/AdminPanel';
import Home from './pages/Home';
import SupplierProfile from './pages/SupplierProfile';
import Suppliers from './pages/Suppliers';
import Notifications from './pages/Notifications';
import OrderDetail from './pages/OrderDetail';
import Orders from './pages/Orders';
import Subscription from './pages/Subscription';
import SubscriptionCheckout from './pages/SubscriptionCheckout';

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="products" element={<Products />} />
        <Route path="product/:id" element={<ProductDetail />} />
        <Route path="suppliers" element={<Suppliers />} />
        <Route path="suppliers/:id" element={<SupplierProfile />} />
        <Route path="notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
        <Route path="wishlist" element={<ProtectedRoute allowedRoles={['buyer']}><Wishlist /></ProtectedRoute>} />
        <Route path="cart" element={<ProtectedRoute allowedRoles={['buyer']}><Cart /></ProtectedRoute>} />
        <Route path="rfq" element={<ProtectedRoute allowedRoles={['buyer']}><RFQList /></ProtectedRoute>} />
        <Route path="rfqs" element={<ProtectedRoute allowedRoles={['buyer']}><RFQList /></ProtectedRoute>} />
        <Route path="rfq/:id" element={<ProtectedRoute><RFQDetail /></ProtectedRoute>} />
        <Route path="rfqs/:id" element={<ProtectedRoute><RFQDetail /></ProtectedRoute>} />
        <Route
          path="orders"
          element={
            <ProtectedRoute allowedRoles={['buyer', 'seller', 'admin']}>
              <Orders />
            </ProtectedRoute>
          }
        />
        <Route path="orders/:id" element={<ProtectedRoute><OrderDetail /></ProtectedRoute>} />
        <Route
          path="seller/subscription"
          element={
            <ProtectedRoute allowedRoles={['seller']}>
              <Subscription />
            </ProtectedRoute>
          }
        />
        <Route
          path="seller/subscription/checkout/:paymentId"
          element={
            <ProtectedRoute allowedRoles={['seller']}>
              <SubscriptionCheckout />
            </ProtectedRoute>
          }
        />
        <Route path="seller/rfqs" element={<ProtectedRoute allowedRoles={['seller']}><SellerRFQs /></ProtectedRoute>} />
        <Route path="seller/orders" element={<Navigate to="/orders" replace />} />
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
