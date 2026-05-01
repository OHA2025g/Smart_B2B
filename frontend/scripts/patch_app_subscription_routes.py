from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "App.jsx"
t = p.read_text("utf-8")
if "Subscription.jsx" in t:
    print("skip")
    raise SystemExit(0)
t = t.replace(
    "import Orders from './pages/Orders';\n",
    "import Orders from './pages/Orders';\nimport Subscription from './pages/Subscription';\nimport SubscriptionCheckout from './pages/SubscriptionCheckout';\n",
    1,
)
ins = """        <Route
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
"""
marker = '        <Route path="seller/rfqs"'
if marker not in t:
    raise SystemExit("marker not found")
t = t.replace(marker, ins + marker, 1)
p.write_text(t, "utf-8")
print("ok")
