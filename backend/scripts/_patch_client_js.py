from pathlib import Path

p = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "api" / "client.js"
t = p.read_text(encoding="utf-8")
if "updatePayment" in t:
    print("client already patched")
    raise SystemExit(0)
t = t.replace(
    "  createFromCart: () => client.post(`${apiBase}/api/rfq/create-from-cart`),",
    "  createFromCart: (data) => client.post(`${apiBase}/api/rfq/create-from-cart`, data),",
    1,
)
t = t.replace(
    "  updateStatus: (id, status) => client.put(`${apiBase}/api/orders/${id}/status`, { status }),\n};",
    "  updateStatus: (id, status) => client.put(`${apiBase}/api/orders/${id}/status`, { status }),\n"
    "  updatePayment: (id, paymentStatus) => client.put(`${apiBase}/api/orders/${id}/payment`, { paymentStatus }),\n"
    "};",
    1,
)
t = t.replace(
    "export const suppliersApi = {\n  getScore:",
    "export const suppliersApi = {\n  list: (params) => client.get(`${apiBase}/api/suppliers`, { params }),\n  getScore:",
    1,
)
t = t.replace(
    "  getLogs: (params) => client.get(`${apiBase}/api/admin/logs`, { params }),\n",
    "  getLogs: (params) => client.get(`${apiBase}/api/admin/logs`, { params }),\n"
    "  getFlaggedMessages: () => client.get(`${apiBase}/api/admin/flagged-messages`),\n",
    1,
)
p.write_text(t, encoding="utf-8")
print("client.js ok")
