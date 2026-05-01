from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "Products.jsx"
t = p.read_text("utf-8")

if "SupplierPlanBadges" in t and "setPlan" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "import { getCategoryImage } from '../utils/getCategoryImage';\n",
    "import { getCategoryImage } from '../utils/getCategoryImage';\nimport { SupplierPlanBadges } from '../components/SupplierPlanBadges';\n",
    1,
)

t = t.replace(
    "  const [filtersOpen, setFiltersOpen] = useState(false);\n",
    "  const [plan, setPlan] = useState('');\n  const [sort, setSort] = useState('recommended');\n  const [filtersOpen, setFiltersOpen] = useState(false);\n",
    1,
)

if "overrides.sort" not in t:
    t = t.replace(
        "    const minP = overrides.min_price !== undefined ? overrides.min_price : minPrice;\n    const maxP = overrides.max_price !== undefined ? overrides.max_price : maxPrice;\n    try {",
        "    const minP = overrides.min_price !== undefined ? overrides.min_price : minPrice;\n    const maxP = overrides.max_price !== undefined ? overrides.max_price : maxPrice;\n    const pln = overrides.plan !== undefined ? overrides.plan : plan;\n    const srt = overrides.sort !== undefined ? overrides.sort : sort;\n    try {",
        1,
    )
    t = t.replace(
        "      if (minP !== '' && minP != null) params.min_price = Number(minP);\n      if (maxP !== '' && maxP != null) params.max_price = Number(maxP);",
        "      if (minP !== '' && minP != null) params.min_price = Number(minP);\n      if (maxP !== '' && maxP != null) params.max_price = Number(maxP);\n      if (pln) params.plan = pln;\n      if (srt) params.sort = srt;",
        1,
    )

t = t.replace(
    "    setMinPrice('');\n    setMaxPrice('');\n    setLoading(true);",
    "    setMinPrice('');\n    setMaxPrice('');\n    setPlan('');\n    setSort('recommended');\n    setLoading(true);",
    1,
)

row = """
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">Supplier plan</label>
              <select
                value={plan}
                onChange={(e) => setPlan(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm bg-white text-slate-800 shadow-sm focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400"
              >
                <option value="">Any</option>
                <option value="free">Free</option>
                <option value="go">GO</option>
                <option value="pro">PRO</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1.5">Sort</label>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm bg-white text-slate-800 shadow-sm focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400"
              >
                <option value="recommended">Recommended</option>
                <option value="pro_first">PRO first</option>
                <option value="newest">Newest</option>
                <option value="price_asc">Price: low to high</option>
                <option value="price_desc">Price: high to low</option>
              </select>
            </div>
          </div>
"""
marker = (
    "            </div>\n"
    "          </div>\n"
    "          <div className=\"flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4 pt-1 border-t border-slate-100\">"
)
if marker in t:
    t = t.replace(
        marker,
        "            </div>\n          </div>\n" + row + "          <div className=\"flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4 pt-1 border-t border-slate-100\">",
        1,
    )
else:
    raise SystemExit("marker for plan row not found")

old_badges = """                          <div className="flex flex-wrap gap-2 items-center">
                            {p.seller?.isVerifiedSupplier ? (
                              <Badge variant="success" className="gap-1">
                                <ShieldCheck className="h-3 w-3" /> Verified
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-slate-500">Unverified</Badge>
                            )}
                            {p.seller?.trustScore != null && (
                              <Badge variant="primary" className="gap-1 font-semibold tabular-nums">
                                <TrendingUp className="h-3 w-3" />
                                {Math.round(p.seller.trustScore)}% score
                              </Badge>
                            )}
                            {p.seller?.trustLevel && (
                              <Badge variant="default">{p.seller.trustLevel}</Badge>
                            )}
                          </div>"""

new_badges = """                          <div className="flex flex-wrap gap-2 items-center">
                            <SupplierPlanBadges
                              plan={p.seller?.subscriptionPlan}
                              verified={p.seller?.isVerifiedSupplier}
                              featured={p.seller?.isFeaturedSupplier}
                              searchBoost={p.seller?.searchBoostLabel}
                              compact
                            />
                            {p.seller?.trustScore != null && (
                              <Badge variant="primary" className="gap-1 font-semibold tabular-nums">
                                <TrendingUp className="h-3 w-3" />
                                {Math.round(p.seller.trustScore)}% score
                              </Badge>
                            )}
                            {p.seller?.trustLevel && (
                              <Badge variant="default">{p.seller.trustLevel}</Badge>
                            )}
                          </div>"""

if old_badges in t:
    t = t.replace(old_badges, new_badges, 1)
else:
    raise SystemExit("badges block not found")

p.write_text(t, "utf-8")
print("ok")
