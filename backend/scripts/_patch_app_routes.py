from pathlib import Path

p = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "App.jsx"
t = p.read_text(encoding="utf-8")
if "import Suppliers" in t:
    print("App already has Suppliers")
    raise SystemExit(0)
t = t.replace(
    "import SupplierProfile from './pages/SupplierProfile';\n",
    "import SupplierProfile from './pages/SupplierProfile';\nimport Suppliers from './pages/Suppliers';\n",
    1,
)
t = t.replace(
    '        <Route path="suppliers/:id" element={<SupplierProfile />} />',
    '        <Route path="suppliers" element={<Suppliers />} />\n'
    '        <Route path="suppliers/:id" element={<SupplierProfile />} />',
    1,
)
# RFQ aliases
t = t.replace(
    "        <Route path=\"rfq\" element={<ProtectedRoute allowedRoles={['buyer']}><RFQList /></ProtectedRoute>} />",
    "        <Route path=\"rfq\" element={<ProtectedRoute allowedRoles={['buyer']}><RFQList /></ProtectedRoute>} />\n"
    "        <Route path=\"rfqs\" element={<ProtectedRoute allowedRoles={['buyer']}><RFQList /></ProtectedRoute>} />",
    1,
)
t = t.replace(
    '        <Route path="rfq/:id" element={<ProtectedRoute><RFQDetail /></ProtectedRoute>} />',
    '        <Route path="rfq/:id" element={<ProtectedRoute><RFQDetail /></ProtectedRoute>} />\n'
    '        <Route path="rfqs/:id" element={<ProtectedRoute><RFQDetail /></ProtectedRoute>} />',
    1,
)
p.write_text(t, encoding="utf-8")
print("App.jsx patched")
