from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "Suppliers.jsx"
t = p.read_text("utf-8")
if "subscriptionPlan" in t or "planFilter" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "import { Badge } from '../components/ui/Badge';\nimport { EmptyState } from '../components/ui/EmptyState';\n",
    "import { Badge } from '../components/ui/Badge';\nimport { EmptyState } from '../components/ui/EmptyState';\nimport { SupplierPlanBadges } from '../components/SupplierPlanBadges';\n",
    1,
)

t = t.replace(
    "  const [sort, setSort] = useState('trust');\n",
    "  const [plan, setPlan] = useState('');\n  const [trustFilter, setTrustFilter] = useState('');\n  const [sort, setSort] = useState('recommended');\n",
    1,
)

t = t.replace(
    """  const params = useMemo(
    () => ({
      search: search.trim() || undefined,
      city: city.trim() || undefined,
      category: category.trim() || undefined,
      verified_only: verifiedOnly || undefined,
      sort,
    }),
    [search, city, category, verifiedOnly, sort],
  );
""",
    """  const params = useMemo(
    () => ({
      search: search.trim() || undefined,
      city: city.trim() || undefined,
      category: category.trim() || undefined,
      verified_only: verifiedOnly || undefined,
      plan: plan || undefined,
      trust_level: trustFilter || undefined,
      sort,
    }),
    [search, city, category, verifiedOnly, plan, trustFilter, sort],
  );
""",
    1,
)

# sort dropdown options
t = t.replace(
    """            <select
              className="border rounded-lg px-2 py-1.5"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="trust">Trust score</option>
              <option value="orders">Orders</option>
              <option value="products">Products</option>
              <option value="name">Name</option>
            </select>""",
    """            <select
              className="border rounded-lg px-2 py-1.5"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="recommended">Recommended</option>
              <option value="pro_first">PRO first</option>
              <option value="trust">Trust score</option>
              <option value="orders">Orders</option>
              <option value="products">Products</option>
              <option value="name">Name</option>
            </select>""",
    1,
)

# Add plan + trust after category row: extend grid
insert = """
          <div className="mt-3 grid sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase">Plan</label>
              <select
                className="mt-1 w-full border rounded-lg px-2 py-1.5 text-sm"
                value={plan}
                onChange={(e) => setPlan(e.target.value)}
              >
                <option value="">All plans</option>
                <option value="free">Free</option>
                <option value="go">GO</option>
                <option value="pro">PRO</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase">Trust level</label>
              <select
                className="mt-1 w-full border rounded-lg px-2 py-1.5 text-sm"
                value={trustFilter}
                onChange={(e) => setTrustFilter(e.target.value)}
              >
                <option value="">Any</option>
                <option value="Highly Trusted">Highly Trusted</option>
                <option value="Trusted">Trusted</option>
                <option value="Moderate">Moderate</option>
                <option value="Low Trust">Low Trust</option>
              </select>
            </div>
          </div>"""

marker = "        <div className=\"mt-3 flex flex-wrap items-center gap-3\">"
if insert.strip() in t:
    pass
elif marker in t:
    t = t.replace(marker, insert + "\n" + marker, 1)
else:
    raise SystemExit("suppliers marker not found")

# supplier card: add plan badges
old = """                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="font-semibold text-lg">{s.companyName || s.name || 'Supplier'}</h2>
                      {s.verified && (
                        <Badge variant="success" className="gap-1">
                          <CheckCircle className="h-3 w-3" /> Verified
                        </Badge>
                      )}
                    </div>"""
new = """                    <div className="space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="font-semibold text-lg">{s.companyName || s.name || 'Supplier'}</h2>
                      </div>
                      <SupplierPlanBadges
                        plan={s.subscriptionPlan}
                        verified={s.verified}
                        featured={s.isFeaturedSupplier}
                        searchBoost={s.searchBoostLabel}
                      />
                    </div>"""
if old in t:
    t = t.replace(old, new, 1)
else:
    raise SystemExit("suppliers title block not found")

p.write_text(t, "utf-8")
print("ok")
