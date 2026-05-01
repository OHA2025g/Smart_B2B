from pathlib import Path

f = Path(__file__).resolve().parent.parent / "src" / "api" / "client.js"
t = f.read_text("utf-8")
o1 = """export const ordersApi = {
  getMy: (params) => client.get(`${apiBase}/api/orders/me`, { params }),
  getById: (id) => client.get(`${apiBase}/api/orders/${id}`),
  getTimeline: (orderId) => client.get(`${apiBase}/api/orders/${orderId}/timeline`),
  updateStatus: (id, status) => client.put(`${apiBase}/api/orders/${id}/status`, { status }),
  updatePayment: (id, paymentStatus) => client.put(`${apiBase}/api/orders/${id}/payment`, { paymentStatus }),
};"""
n1 = """export const ordersApi = {
  getMy: (params) => client.get(`${apiBase}/api/orders/me`, { params }),
  getById: (id) => client.get(`${apiBase}/api/orders/${id}`),
  getTimeline: (orderId) => client.get(`${apiBase}/api/orders/${orderId}/timeline`),
  updateStatus: (id, status) => client.put(`${apiBase}/api/orders/${id}/status`, { status }),
  updatePayment: (id, paymentStatus) => client.put(`${apiBase}/api/orders/${id}/payment`, { paymentStatus }),
  getPayments: (orderId) => client.get(`${apiBase}/api/orders/${orderId}/payments`),
  initiatePayment: (orderId) => client.post(`${apiBase}/api/orders/${orderId}/payments/initiate`, {}),
  simulateOrderPayment: (orderId, paymentId, body) =>
    client.post(`${apiBase}/api/orders/${orderId}/payments/${paymentId}/simulate`, body),
  releaseEscrow: (orderId) => client.post(`${apiBase}/api/orders/${orderId}/payments/release`, {}),
};

export const subscriptionApi = {
  getPlans: () => client.get(`${apiBase}/api/subscriptions/plans`),
  getMe: () => client.get(`${apiBase}/api/subscriptions/me`),
  checkout: (body) => client.post(`${apiBase}/api/subscriptions/checkout`, body),
  simulate: (paymentId, body) =>
    client.post(`${apiBase}/api/subscriptions/payment/${paymentId}/simulate`, body),
};"""
if o1 not in t:
    raise SystemExit("ordersApi block not found")
t = t.replace(o1, n1, 1)
admin = """  getAnalyticsOrderTrends: () => client.get(`${apiBase}/api/admin/analytics/order-trends`),
};"""
admin_r = """  getAnalyticsOrderTrends: () => client.get(`${apiBase}/api/admin/analytics/order-trends`),
  getSubscriptions: () => client.get(`${apiBase}/api/admin/subscriptions`),
  getPayments: () => client.get(`${apiBase}/api/admin/payments`),
  getRevenueSummary: () => client.get(`${apiBase}/api/admin/revenue-summary`),
};"""
if admin not in t:
    raise SystemExit("admin block not found")
t = t.replace(admin, admin_r, 1)
f.write_text(t, "utf-8")
print("ok")
