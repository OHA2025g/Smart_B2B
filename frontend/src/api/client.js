import axios from 'axios';

/** localStorage keys — keep in sync with AuthContext */
export const AUTH_TOKEN_KEY = 'token';
export const AUTH_USER_KEY = 'smartb2b_user';

// When empty, Vite proxy forwards /api to backend (localhost:5000)
const baseURL = import.meta.env.VITE_API_URL || '';

const client = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT from localStorage to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 - clear token and redirect to login
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_USER_KEY);
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// Path prefix: when baseURL empty, Vite proxy sends /api to backend; paths must be /api/...
const apiBase = baseURL ? baseURL : '';

export const publicApi = {
  marketStats: () => client.get(`${apiBase}/api/public/stats`),
};

export const authApi = {
  register: (data) => client.post(`${apiBase}/api/auth/register`, data),
  login: (data) => client.post(`${apiBase}/api/auth/login`, data),
  me: () => client.get(`${apiBase}/api/auth/me`),
};

export const companyApi = {
  upsert: (data) => client.post(`${apiBase}/api/company`, data),
  getMe: () => client.get(`${apiBase}/api/company/me`),
};

export const productsApi = {
  list: (params) => client.get(`${apiBase}/api/products`, { params }),
  listMy: () => client.get(`${apiBase}/api/products/seller/me`),
  getById: (id) => client.get(`${apiBase}/api/products/${id}`),
  create: (data) => client.post(`${apiBase}/api/products`, data),
  update: (id, data) => client.put(`${apiBase}/api/products/${id}`, data),
  delete: (id) => client.delete(`${apiBase}/api/products/${id}`),
};

export const inquiriesApi = {
  create: (data) => client.post(`${apiBase}/api/inquiries`, data),
  getMe: () => client.get(`${apiBase}/api/inquiries/me`),
};

export const categoriesApi = {
  list: () => client.get(`${apiBase}/api/categories`),
  create: (data) => client.post(`${apiBase}/api/categories`, data),
  update: (id, data) => client.put(`${apiBase}/api/categories/${id}`, data),
  delete: (id) => client.delete(`${apiBase}/api/categories/${id}`),
};

export const wishlistApi = {
  get: () => client.get(`${apiBase}/api/wishlist`),
  toggle: (productId) => client.post(`${apiBase}/api/wishlist/${productId}`),
  remove: (productId) => client.delete(`${apiBase}/api/wishlist/${productId}`),
};

export const cartApi = {
  get: () => client.get(`${apiBase}/api/cart`),
  add: (data) => client.post(`${apiBase}/api/cart`, data),
  update: (productId, data) => client.put(`${apiBase}/api/cart/${productId}`, data),
  remove: (productId) => client.delete(`${apiBase}/api/cart/${productId}`),
  clear: () => client.post(`${apiBase}/api/cart/clear`),
};

export const rfqApi = {
  create: (data) => client.post(`${apiBase}/api/rfq`, data),
  createFromCart: (data) => client.post(`${apiBase}/api/rfq/create-from-cart`, data),
  getMy: () => client.get(`${apiBase}/api/rfq/me`),
  getAssigned: () => client.get(`${apiBase}/api/rfq/assigned`),
  getById: (id) => client.get(`${apiBase}/api/rfq/${id}`),
  updateStatus: (id, status) => client.put(`${apiBase}/api/rfq/${id}/status`, { status }),
  getQuotes: (rfqId) => client.get(`${apiBase}/api/rfq/${rfqId}/quotes`),
  getQuoteComparison: (rfqId) => client.get(`${apiBase}/api/rfq/${rfqId}/quote-comparison`),
  getTimeline: (rfqId) => client.get(`${apiBase}/api/rfq/${rfqId}/timeline`),
  submitQuote: (rfqId, data) => client.post(`${apiBase}/api/rfq/${rfqId}/quote`, data),
  acceptQuote: (rfqId, quoteId) => client.post(`${apiBase}/api/rfq/${rfqId}/accept-quote/${quoteId}`),
  rejectQuote: (rfqId, quoteId) => client.post(`${apiBase}/api/rfq/${rfqId}/reject-quote/${quoteId}`),
  getCounterOffers: (rfqId) => client.get(`${apiBase}/api/rfq/${rfqId}/counter-offers`),
  postCounterOffer: (rfqId, data) => client.post(`${apiBase}/api/rfq/${rfqId}/counter-offer`, data),
};

export const quoteApi = {
  update: (id, data) => client.put(`${apiBase}/api/quote/${id}`, data),
};

export const ordersApi = {
  getMy: (params) => client.get(`${apiBase}/api/orders/me`, { params }),
  getById: (id) => client.get(`${apiBase}/api/orders/${id}`),
  getTimeline: (orderId) => client.get(`${apiBase}/api/orders/${orderId}/timeline`),
  updateStatus: (id, status) => client.put(`${apiBase}/api/orders/${id}/status`, { status }),
  updatePayment: (id, paymentStatus) => client.put(`${apiBase}/api/orders/${id}/payment`, { paymentStatus }),
};

export const messagesApi = {
  get: (rfqId) => client.get(`${apiBase}/api/messages/${rfqId}`),
  post: (rfqId, text, opts = {}) =>
    client.post(`${apiBase}/api/messages/${rfqId}`, {
      text,
      ...(opts.confirmSend ? { confirm_send: true } : {}),
    }),
};

export const adminApi = {
  summary: () => client.get(`${apiBase}/api/admin/summary`),
  dashboard: () => client.get(`${apiBase}/api/admin/dashboard`),
  getUsers: () => client.get(`${apiBase}/api/admin/users`),
  getUserProfile: (id) => client.get(`${apiBase}/api/admin/user-profile/${id}`),
  banUser: (id, banned) => client.put(`${apiBase}/api/admin/users/${id}/ban`, { banned }),
  unbanUser: (id) => client.put(`${apiBase}/api/admin/users/${id}/unban`),
  verifySupplier: (id, verified) => client.put(`${apiBase}/api/admin/users/${id}/verify-supplier`, { verified }),
  verifySupplierPost: (sellerId) => client.post(`${apiBase}/api/admin/suppliers/${sellerId}/verify`),
  unverifySupplier: (sellerId) => client.put(`${apiBase}/api/admin/suppliers/${sellerId}/unverify`),
  recalculateScore: (sellerId) => client.post(`${apiBase}/api/admin/suppliers/${sellerId}/recalculate-score`),
  getSuppliers: () => client.get(`${apiBase}/api/admin/suppliers`),
  getCategories: () => client.get(`${apiBase}/api/admin/categories`),
  getRfqs: (params) => client.get(`${apiBase}/api/admin/rfqs`, { params }),
  getOrders: () => client.get(`${apiBase}/api/admin/orders`),
  getLogs: (params) => client.get(`${apiBase}/api/admin/logs`, { params }),
  getFlaggedMessages: () => client.get(`${apiBase}/api/admin/flagged-messages`),
  getModerationMessages: () => client.get(`${apiBase}/api/admin/moderation/messages`),
  getAnalyticsOverview: () => client.get(`${apiBase}/api/admin/analytics/overview`),
  getAnalyticsTopSuppliers: () => client.get(`${apiBase}/api/admin/analytics/top-suppliers`),
  getAnalyticsCategoryPerformance: () => client.get(`${apiBase}/api/admin/analytics/category-performance`),
  getAnalyticsTopProducts: () => client.get(`${apiBase}/api/admin/analytics/top-products`),
  getAnalyticsRfqTrends: () => client.get(`${apiBase}/api/admin/analytics/rfq-trends`),
  getAnalyticsOrderTrends: () => client.get(`${apiBase}/api/admin/analytics/order-trends`),
};

export const suppliersApi = {
  list: (params) => client.get(`${apiBase}/api/suppliers`, { params }),
  getScore: (sellerId) => client.get(`${apiBase}/api/suppliers/${sellerId}/score`),
  getProfile: (sellerId) => client.get(`${apiBase}/api/suppliers/${sellerId}/profile`),
};

export const notificationsApi = {
  getMe: () => client.get(`${apiBase}/api/notifications/me`),
  markRead: (id) => client.put(`${apiBase}/api/notifications/${id}/read`),
  markAllRead: () => client.put(`${apiBase}/api/notifications/read-all`),
};

export const sellerDashboardApi = {
  get: () => client.get(`${apiBase}/api/seller/dashboard`),
};

export const buyerDashboardApi = {
  get: () => client.get(`${apiBase}/api/buyer/dashboard`),
};

export default client;
