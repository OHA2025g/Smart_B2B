"""One-off production cleanup: patch frontend files. Run from repo root: python backend/scripts/_cleanup_production.py"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def patch_admin_panel():
    p = ROOT / "frontend" / "src" / "pages" / "AdminPanel.jsx"
    t = p.read_text(encoding="utf-8")
    if "getFlaggedMessages" in t and "tab === 'moderation'" in t:
        print("AdminPanel already updated")
        return
    t = t.replace(
        "import { Users, FolderOpen, FileText, Package, Activity, LayoutDashboard, ShieldCheck, Settings2 } from 'lucide-react';\nimport { adminApi } from '../api/client';",
        "import { Users, FolderOpen, FileText, Package, Activity, LayoutDashboard, ShieldCheck, Settings2, Flag } from 'lucide-react';\nimport { adminApi, categoriesApi } from '../api/client';",
    )
    t = t.replace("import { categoriesApi } from '../api/client';\n\n", "\n")
    if "import { adminApi, categoriesApi }" not in t:
        raise SystemExit("import merge failed")
    old_tabs = """const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'suppliers', label: 'Supplier verification', icon: ShieldCheck },
  { id: 'categories', label: 'Categories', icon: FolderOpen },
  { id: 'rfqs', label: 'RFQs', icon: FileText },
  { id: 'orders', label: 'Orders', icon: Package },
  { id: 'logs', label: 'Activity Logs', icon: Activity },
];"""
    new_tabs = """const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'suppliers', label: 'Supplier verification', icon: ShieldCheck },
  { id: 'categories', label: 'Categories', icon: FolderOpen },
  { id: 'rfqs', label: 'RFQs', icon: FileText },
  { id: 'orders', label: 'Orders', icon: Package },
  { id: 'moderation', label: 'Moderation', icon: Flag },
  { id: 'logs', label: 'Activity Logs', icon: Activity },
];"""
    t = t.replace(old_tabs, new_tabs)
    t = t.replace(
        "  const [logs, setLogs] = useState([]);\n  const [loading, setLoading] = useState(true);",
        "  const [logs, setLogs] = useState([]);\n  const [flaggedMessages, setFlaggedMessages] = useState([]);\n  const [loading, setLoading] = useState(true);",
    )
    old_p = """      const [d, u, sup, c, r, o, l] = await Promise.all([
        adminApi.dashboard().then((res) => res.data.data.dashboard).catch(() => null),
        adminApi.getUsers().then((res) => res.data.data.users),
        adminApi.getSuppliers().then((res) => res.data.data.suppliers).catch(() => []),
        adminApi.getCategories().then((res) => res.data.data.categories || []).catch(() => []),
        adminApi.getRfqs().then((res) => res.data.data.rfqs),
        adminApi.getOrders().then((res) => res.data.data.orders),
        adminApi.getLogs().then((res) => res.data.data.logs),
      ]);
      setDashboard(d || null);
      setUsers(u || []);
      setSuppliers(sup || []);
      setCategories(c || []);
      setRfqs(r || []);
      setOrders(o || []);
      setLogs(l || []);"""
    new_p = """      const [d, u, sup, c, r, o, l, fm] = await Promise.all([
        adminApi.dashboard().then((res) => res.data.data.dashboard).catch(() => null),
        adminApi.getUsers().then((res) => res.data.data.users),
        adminApi.getSuppliers().then((res) => res.data.data.suppliers).catch(() => []),
        adminApi.getCategories().then((res) => res.data.data.categories || []).catch(() => []),
        adminApi.getRfqs().then((res) => res.data.data.rfqs),
        adminApi.getOrders().then((res) => res.data.data.orders),
        adminApi.getLogs().then((res) => res.data.data.logs),
        adminApi.getFlaggedMessages().then((res) => res.data.data.flagged || []).catch(() => []),
      ]);
      setDashboard(d || null);
      setUsers(u || []);
      setSuppliers(sup || []);
      setCategories(c || []);
      setRfqs(r || []);
      setOrders(o || []);
      setLogs(l || []);
      setFlaggedMessages(Array.isArray(fm) ? fm : []);"""
    t = t.replace(old_p, new_p)
    t = t.replace(
        "  useEffect(() => {\n    load();\n  }, []);",
        "  useEffect(() => {\n    load();\n    // Initial load only; tab actions call load() explicitly.\n    // eslint-disable-next-line react-hooks/exhaustive-deps\n  }, []);",
    )
    # Insert moderation section before logs section
    mark = "      {tab === 'logs' && ("
    if mark not in t:
        raise SystemExit("logs marker not found")
    mod_block = """      {tab === 'moderation' && (
        <Card>
          <div className="px-5 py-4 border-b border-slate-100">
            <h2 className="section-title">Flagged RFQ messages</h2>
            <p className="text-sm text-slate-500 mt-1">
              Contact-sharing attempts (demo moderation). No message text is hidden here for admin review.
            </p>
          </div>
          <div className="p-4 overflow-x-auto">
            {!flaggedMessages?.length ? (
              <p className="text-sm text-slate-500">No flagged messages</p>
            ) : (
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                    <th className="py-2 pr-3">RFQ</th>
                    <th className="py-2 pr-3">Role</th>
                    <th className="py-2 pr-3">Flag</th>
                    <th className="py-2 pr-3">Reason</th>
                    <th className="py-2">Excerpt</th>
                  </tr>
                </thead>
                <tbody>
                  {flaggedMessages.map((row, i) => (
                    <tr key={row.messageId || i} className="border-b border-slate-50">
                      <td className="py-2 pr-3 font-mono text-xs">
                        {row.rfqId ? <Link to={`/rfq/${row.rfqId}`} className="text-teal-700 hover:underline">{row.rfqId}</Link> : '—'}
                      </td>
                      <td className="py-2 pr-3">{row.senderRole || '—'}</td>
                      <td className="py-2 pr-3">
                        {row.moderationFlag ? <Badge variant="warning">Flagged</Badge> : '—'}
                      </td>
                      <td className="py-2 pr-3 text-slate-600">{(row.moderationReason || '—').slice(0, 80)}</td>
                      <td className="py-2 text-slate-500 max-w-md truncate" title={row.text}>
                        {row.text || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      )}

"""
    t = t.replace(mark, mod_block + mark, 1)
    p.write_text(t, encoding="utf-8")
    print("AdminPanel patched")


def patch_products_lint():
    p = ROOT / "frontend" / "src" / "pages" / "Products.jsx"
    t = p.read_text(encoding="utf-8")
    if "eslint-disable-next-line react-hooks/exhaustive-deps" in t and "fetchProducts" in t:
        old = "  useEffect(() => {\n    fetchProducts();\n  }, [verifiedOnly]);"
        new = "  useEffect(() => {\n    fetchProducts();\n    // eslint-disable-next-line react-hooks/exhaustive-deps\n  }, [verifiedOnly]);"
        if old in t:
            t = t.replace(old, new, 1)
            p.write_text(t, encoding="utf-8")
            print("Products useEffect noted")
        else:
            print("Products pattern skip")


def write_readme_append():
    """Append/refresh 'Quick start' and production checklist if not present."""
    p = ROOT / "README.md"
    t = p.read_text(encoding="utf-8")
    marker = "## Quick start (production-style)"
    if marker in t:
        print("README quick start present")
        return
    block = """
---

## Quick start (production-style)

### Prerequisites
- **Python 3.11+**
- **Node 18+**
- **MongoDB** (local or Atlas URI in `backend/.env`)

### Backend
```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate   # Windows
pip install -r requirements.txt
# copy .env.example to .env and set MONGODB_URI / JWT_SECRET
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database seed (demo users + baseline data)
```bash
cd backend
python scripts/seed.py
# optional large demo set:
python scripts/generate_demo_data.py
```

**Demo logins (after `seed.py`):**
| Role | Email | Password |
|------|--------|----------|
| Admin | `admin@smartb2b.com` | `Admin@123` |
| Seller | `seller@example.com` | `Seller@123` |
| Buyer | `buyer@example.com` | `Buyer@123` |

### Frontend
```bash
cd frontend
npm install
# dev: Vite proxy uses /api — run backend on same machine or set VITE_API_URL
npm run dev
# production bundle
npm run build
```

### Docker
Use `docker-compose.yml` at the repo root if you prefer an all-in-one stack; ensure env vars match `backend` settings.

### Smoke test
- `cd frontend && npm run build && npm run lint`
- `cd backend && python -c "from app.main import app; print('ok', app.title)"`
- Log in as buyer → RFQ cart → create RFQ → (seller) quote → (buyer) accept → order → print invoice; admin → panel & logs.
"""
    # Insert after first ## Tech stack section or at end of intro - we append before "## Tech stack" is wrong. Append at end of file
    t = t.rstrip() + "\n" + block
    p.write_text(t, encoding="utf-8")
    print("README appended quick start")


def update_demo_checklist():
    p = ROOT / "FINAL_DEMO_CHECKLIST.md"
    t = p.read_text(encoding="utf-8")
    add = "\n## Production smoke (automated)\n\n- [ ] `frontend`: `npm run build` (no errors), `npm run lint` (warnings \u2264 10 in this repo).\n- [ ] `backend`: `python -c \"from app.main import app\"` from `backend/`.\n- [ ] Admin **Moderation** tab loads flagged messages (may be empty).\n- [ ] Order **Print** uses browser print; navbar hidden in print CSS on order page.\n"
    if "Production smoke (automated)" in t:
        print("checklist has smoke section")
        return
    p.write_text(t.rstrip() + add, encoding="utf-8")
    print("FINAL_DEMO_CHECKLIST updated")


if __name__ == "__main__":
    patch_admin_panel()
    patch_products_lint()
    write_readme_append()
    update_demo_checklist()
    print("done")
