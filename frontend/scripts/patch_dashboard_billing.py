from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "Dashboard.jsx"
t = p.read_text("utf-8")
if "adminRevenue" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "  const [adminRfqTrends, setAdminRfqTrends] = useState([]);\n  const [adminOrderTrends, setAdminOrderTrends] = useState([]);",
    "  const [adminRfqTrends, setAdminRfqTrends] = useState([]);\n  const [adminOrderTrends, setAdminOrderTrends] = useState([]);\n  const [adminRevenue, setAdminRevenue] = useState(null);",
    1,
)

t = t.replace(
    """        if (user?.role === 'admin') {
          const [summaryRes, dashboardRes, tr, tor] = await Promise.all([
            adminApi.summary().catch(() => ({ data: { data: { summary: null } } })),
            adminApi.dashboard().catch(() => ({ data: { data: { dashboard: null } } })),
            adminApi.getAnalyticsRfqTrends().catch(() => ({ data: { data: { rfqTrends: [] } } })),
            adminApi.getAnalyticsOrderTrends().catch(() => ({ data: { data: { orderTrends: [] } } })),
          ]);""",
    """        if (user?.role === 'admin') {
          const [summaryRes, dashboardRes, tr, tor, rev] = await Promise.all([
            adminApi.summary().catch(() => ({ data: { data: { summary: null } } })),
            adminApi.dashboard().catch(() => ({ data: { data: { dashboard: null } } })),
            adminApi.getAnalyticsRfqTrends().catch(() => ({ data: { data: { rfqTrends: [] } } })),
            adminApi.getAnalyticsOrderTrends().catch(() => ({ data: { data: { orderTrends: [] } } })),
            adminApi.getRevenueSummary().catch(() => ({ data: { data: { revenue: null } } })),
          ]);""",
    1,
)

t = t.replace(
    "          setAdminRfqTrends(tr.data?.data?.rfqTrends || []);\n          setAdminOrderTrends(tor.data?.data?.orderTrends || []);",
    "          setAdminRfqTrends(tr.data?.data?.rfqTrends || []);\n          setAdminOrderTrends(tor.data?.data?.orderTrends || []);\n          setAdminRevenue(rev.data?.data?.revenue || null);",
    1,
)

# import Link
if "import { Link }" not in t:
    t = t.replace("import { useState, useEffect, useMemo } from 'react';\n", "import { useState, useEffect, useMemo } from 'react';\nimport { Link } from 'react-router-dom';\n", 1)
elif "from 'react-router-dom'" in t and "Link" not in t.split("react-router-dom")[0][-200:]:
    t = t.replace("import { useNavigate }", "import { useNavigate, Link }", 1)  # fallback

# StatCard row after orders - insert revenue minigrid
marker = "                <StatCard title=\"Orders\" value={adminDashboard.totalOrders} icon={Package} />\n              </>\n            )}\n          </div>"
if marker not in t:
    raise SystemExit("admin stat marker not found")

insert = """                <StatCard title="Orders" value={adminDashboard.totalOrders} icon={Package} />
              </>
            )}
            {adminRevenue && (
              <>
                <StatCard
                  title="Sub revenue (demo) ₹"
                  value={adminRevenue.subscription_revenue_inr ?? 0}
                  icon={TrendingUp}
                />
                <StatCard
                  title="Escrow vol. (demo) ₹"
                  value={adminRevenue.escrow_payment_volume_inr ?? 0}
                  icon={Activity}
                />
                <StatCard title="OK payments" value={adminRevenue.successful_payments ?? 0} icon={Package} />
                <StatCard title="Failed pays" value={adminRevenue.failed_payments ?? 0} icon={MessageSquare} />
                <StatCard title="Active GO" value={adminRevenue.active_go_sellers ?? 0} icon={Users} />
                <StatCard title="Active PRO" value={adminRevenue.active_pro_sellers ?? 0} icon={Users} />
              </>
            )}
          </div>"""
t = t.replace(marker, insert, 1)

# Seller section: find seller workspace content - add Card after motion hero
# Simpler: add block after "user?.role === 'seller' &&" grid - search for "sellerStats"
seller_marker = "      {user?.role === 'seller' && (sellerDashboard || sellerStats.rfqs > 0"
if "seller plan" in t or "currentPlan" in t and "Link to=/seller/subscription" in t:
    pass
idx = t.find(seller_marker)
if idx == -1:
    # try alternative
    seller_marker2 = "{user?.role === 'seller' &&"
    # insert small card right after the hero (before first seller chart)
    m2 = "    </motion.div>\n\n      {user?.role === 'admin' && (adminSummary || adminDashboard) && ("
    if m2 in t and 'seller/subscription' not in t:
        t = t.replace(
            m2,
            """    </motion.div>

      {user?.role === 'seller' && sellerDashboard?.currentPlan && (
        <Card className="mb-8 border-teal-100">
          <CardHeader>
            <span className="section-title">Your plan</span>
          </CardHeader>
          <CardBody>
            <p className="text-slate-800 font-semibold capitalize text-lg">
              {sellerDashboard.currentPlan.name} plan
            </p>
            <p className="text-sm text-slate-500 mt-1">
              RFQs visible to your catalog: use Subscription to upgrade to GO/PRO.
            </p>
            <Link
              to="/seller/subscription"
              className="mt-3 inline-block text-sm font-semibold text-teal-600 hover:text-teal-800"
            >
              Manage subscription →
            </Link>
          </CardBody>
        </Card>
      )}

      {user?.role === 'admin' && (adminSummary || adminDashboard) && (""",
            1,
        )
else:
    pass

# Buyer: add mini stats for pending/escrow after hero - same pattern
if "escrowHeldOrders" not in t and "pendingPayments" in t:
    pass
m3 = "    </motion.div>\n\n      {user?.role === 'admin' && (adminSummary || adminDashboard) && ("
# If we already replaced for seller, m3 might differ
m4 = "      {user?.role === 'buyer' && (buyerStats.rfqs > 0"
if m3 in t and "escrowHeldOrders" not in t and "user?.role === 'buyer'" in t:
    t = t.replace(
        "    </motion.div>\n\n      {user?.role === 'seller' && sellerDashboard",
        "    </motion.div>\n\n      {user?.role === 'buyer' && buyerDashboard && (buyerDashboard.pendingPayments > 0 || buyerDashboard.escrowHeldOrders > 0) && (\n        <div className=\"grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8\">\n          <StatCard title=\"Pending payment actions\" value={buyerDashboard.pendingPayments ?? 0} icon={Package} />\n          <StatCard title=\"Orders in escrow (demo)\" value={buyerDashboard.escrowHeldOrders ?? 0} icon={MessageSquare} />\n        </div>\n      )}\n\n      {user?.role === 'seller' && sellerDashboard",
        1,
    )

p.write_text(t, "utf-8")
print("ok")
