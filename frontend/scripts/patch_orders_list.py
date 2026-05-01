from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "Orders.jsx"
t = p.read_text("utf-8")
if "payFilter" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "import { Badge } from '../components/ui/Badge';\nimport { Input } from '../components/ui/Input';\n",
    "import { Badge } from '../components/ui/Badge';\nimport { paymentStatusLabel } from '../components/SupplierPlanBadges';\nimport { Input } from '../components/ui/Input';\n",
    1,
)

t = t.replace(
    "  const [search, setSearch] = useState('');\n",
    "  const [search, setSearch] = useState('');\n  const [payFilter, setPayFilter] = useState('');\n",
    1,
)

# extend useEffect dependency and params
t = t.replace(
    "    const p =\n      user?.role === 'admin'\n        ? adminApi.getOrders()\n        : ordersApi.getMy(status ? { status } : undefined);",
    "    const orderParams = {};\n    if (status) orderParams.status = status;\n    if (payFilter) orderParams.payment_status = payFilter;\n    const p =\n      user?.role === 'admin'\n        ? adminApi.getOrders()\n        : ordersApi.getMy(Object.keys(orderParams).length ? orderParams : undefined);",
    1,
)

t = t.replace("  }, [user?.role, status]);", "  }, [user?.role, status, payFilter]);", 1)

# add payment filter in UI: after order status select
old = """          <div className="sm:w-48">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value || 'all'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>"""

new = """          <div className="sm:w-48">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value || 'all'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="sm:w-48">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Payment</label>
            <select
              value={payFilter}
              onChange={(e) => setPayFilter(e.target.value)}
              className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              <option value="">All</option>
              <option value="payment_pending">Payment pending</option>
              <option value="initiated">Initiated</option>
              <option value="escrow_held">Escrow held</option>
              <option value="payment_failed">Failed</option>
              <option value="released">Released</option>
              <option value="refunded">Refunded</option>
            </select>
          </div>"""
if old not in t:
    raise SystemExit("status block not found for orders list")
t = t.replace(old, new, 1)

# In admin branch filtered by status, also filter payment when payFilter
t = t.replace(
    "    if (user?.role === 'admin' && status) {\n      list = list.filter((o) => o.status === status);\n    }",
    "    if (user?.role === 'admin' && status) {\n      list = list.filter((o) => o.status === status);\n    }\n    if (payFilter) {\n      list = list.filter((o) => (o.paymentStatus || 'payment_pending') === payFilter);\n    }",
    1,
)

# badge: add second badge
t = t.replace(
    """                    <Badge variant={badgeVariant(o.status)} className="capitalize font-semibold">
                      {o.status}
                    </Badge>""",
    """                    <Badge variant={badgeVariant(o.status)} className="capitalize font-semibold">
                      Order: {o.status}
                    </Badge>
                    <Badge variant="outline" className="text-xs font-medium border-slate-200">
                      {paymentStatusLabel(o.paymentStatus)}
                    </Badge>""",
    1,
)

# filtered useMemo - add payFilter
t = t.replace("  }, [orders, search, status, user?.role]);", "  }, [orders, search, status, payFilter, user?.role]);", 1)

p.write_text(t, "utf-8")
print("ok")
