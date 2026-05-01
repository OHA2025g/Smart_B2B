from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "AdminPanel.jsx"
t = p.read_text("utf-8")
if "tab === 'billing'" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "import { Users, FolderOpen, FileText, Package, Activity, LayoutDashboard, ShieldCheck, Settings2, Flag, X, ExternalLink, Search } from 'lucide-react';\n",
    "import { Users, FolderOpen, FileText, Package, Activity, LayoutDashboard, ShieldCheck, Settings2, Flag, X, ExternalLink, Search, CreditCard, TrendingUp } from 'lucide-react';\n",
    1,
)

t = t.replace(
    "  { id: 'orders', label: 'Orders', icon: Package },\n  { id: 'moderation', label: 'Moderation', icon: Flag },\n",
    "  { id: 'orders', label: 'Orders', icon: Package },\n  { id: 'billing', label: 'Billing & revenue', icon: CreditCard },\n  { id: 'moderation', label: 'Moderation', icon: Flag },\n",
    1,
)

t = t.replace(
    "  const [flaggedMessages, setFlaggedMessages] = useState([]);\n  const [loading, setLoading] = useState(true);\n",
    "  const [flaggedMessages, setFlaggedMessages] = useState([]);\n  const [subscriptions, setSubscriptions] = useState([]);\n  const [payments, setPayments] = useState([]);\n  const [revenue, setRevenue] = useState(null);\n  const [loading, setLoading] = useState(true);\n",
    1,
)

t = t.replace(
    """      const [d, u, sup, c, r, o, l, mm] = await Promise.all([
        adminApi.dashboard().then((res) => res.data.data.dashboard).catch(() => null),
        adminApi.getUsers().then((res) => res.data.data.users),
        adminApi.getSuppliers().then((res) => res.data.data.suppliers).catch(() => []),
        adminApi.getCategories().then((res) => res.data.data.categories || []).catch(() => []),
        adminApi.getRfqs().then((res) => res.data.data.rfqs),
        adminApi.getOrders().then((res) => res.data.data.orders),
        adminApi.getLogs().then((res) => res.data.data.logs),
        adminApi.getModerationMessages().then((res) => res.data.data.messages || []).catch(() => []),
      ]);""",
    """      const [d, u, sup, c, r, o, l, mm, sub, pay, rev] = await Promise.all([
        adminApi.dashboard().then((res) => res.data.data.dashboard).catch(() => null),
        adminApi.getUsers().then((res) => res.data.data.users),
        adminApi.getSuppliers().then((res) => res.data.data.suppliers).catch(() => []),
        adminApi.getCategories().then((res) => res.data.data.categories || []).catch(() => []),
        adminApi.getRfqs().then((res) => res.data.data.rfqs),
        adminApi.getOrders().then((res) => res.data.data.orders),
        adminApi.getLogs().then((res) => res.data.data.logs),
        adminApi.getModerationMessages().then((res) => res.data.data.messages || []).catch(() => []),
        adminApi.getSubscriptions().then((res) => res.data.data.subscriptions || []).catch(() => []),
        adminApi.getPayments().then((res) => res.data.data.payments || []).catch(() => []),
        adminApi.getRevenueSummary().then((res) => res.data.data.revenue).catch(() => null),
      ]);""",
    1,
)

t = t.replace(
    "      setFlaggedMessages(Array.isArray(mm) ? mm : []);",
    "      setFlaggedMessages(Array.isArray(mm) ? mm : []);\n      setSubscriptions(sub || []);\n      setPayments(pay || []);\n      setRevenue(rev || null);",
    1,
)

# insert panel before moderation section
marker = "      {tab === 'moderation' && ("
if marker not in t:
    raise SystemExit("moderation marker not found")

panel = r"""      {tab === 'billing' && (
        <div className="space-y-6">
          {revenue && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card className="p-4 border-emerald-100">
                <p className="text-xs font-semibold text-slate-500 uppercase">Subscription revenue (INR, demo)</p>
                <p className="text-2xl font-bold text-emerald-700">₹{revenue.subscription_revenue_inr}</p>
              </Card>
              <Card className="p-4 border-sky-100">
                <p className="text-xs font-semibold text-slate-500 uppercase">Escrow volume (INR, demo)</p>
                <p className="text-2xl font-bold text-sky-700">₹{revenue.escrow_payment_volume_inr}</p>
              </Card>
              <Card className="p-4">
                <p className="text-xs font-semibold text-slate-500">Successful / failed</p>
                <p className="text-lg font-bold text-slate-800">
                  {revenue.successful_payments} / {revenue.failed_payments}
                </p>
              </Card>
              <Card className="p-4">
                <p className="text-xs font-semibold text-slate-500">Sellers: GO / PRO / free</p>
                <p className="text-sm text-slate-800">
                  {revenue.sellers_by_plan_go} GO, {revenue.sellers_by_plan_pro} PRO, {revenue.sellers_by_plan_free} free
                </p>
              </Card>
              <Card className="p-4">
                <p className="text-xs font-semibold text-slate-500">Active subs (rows)</p>
                <p className="text-sm">
                  GO {revenue.active_go_sellers} · PRO {revenue.active_pro_sellers}
                </p>
              </Card>
            </div>
          )}
          <Card>
            <div className="px-4 py-3 border-b border-slate-100">
              <h2 className="section-title">Seller subscriptions (demo)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500">
                    <th className="p-2">Seller</th>
                    <th className="p-2">Plan</th>
                    <th className="p-2">Status</th>
                    <th className="p-2">Started</th>
                    <th className="p-2">Expires</th>
                  </tr>
                </thead>
                <tbody>
                  {subscriptions.slice(0, 200).map((s) => (
                    <tr key={s._id} className="border-b border-slate-50">
                      <td className="p-2">{s.sellerEmail || s.sellerName || '—'}</td>
                      <td className="p-2 capitalize">{s.plan}</td>
                      <td className="p-2">{s.status}</td>
                      <td className="p-2 text-xs">{s.startedAt ? formatDateTimeIst(s.startedAt) : '—'}</td>
                      <td className="p-2 text-xs">{s.expiresAt ? formatDateTimeIst(s.expiresAt) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <Card>
            <div className="px-4 py-3 border-b border-slate-100">
              <h2 className="section-title">Payments (demo)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500">
                    <th className="p-2">Id</th>
                    <th className="p-2">User</th>
                    <th className="p-2">Type</th>
                    <th className="p-2">₹</th>
                    <th className="p-2">Status</th>
                    <th className="p-2">Method</th>
                    <th className="p-2">When</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.slice(0, 200).map((p) => (
                    <tr key={p._id} className="border-b border-slate-50">
                      <td className="p-2 font-mono text-xs">{(p._id || p.id || '').toString().slice(-8)}</td>
                      <td className="p-2">{p.userEmail || p.userName || '—'}</td>
                      <td className="p-2">{p.paymentType}</td>
                      <td className="p-2">{p.amount}</td>
                      <td className="p-2">{p.status}</td>
                      <td className="p-2">{p.method || '—'}</td>
                      <td className="p-2 text-xs">{p.createdAt ? formatDateTimeIst(p.createdAt) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

"""
t = t.replace(marker, panel + "\n" + marker, 1)
p.write_text(t, "utf-8")
print("ok")
