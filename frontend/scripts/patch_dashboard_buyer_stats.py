from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "Dashboard.jsx"
t = p.read_text("utf-8")
if "escrowHeldOrders" in t:
    print("skip")
    raise SystemExit(0)

m = "      {user?.role === 'admin' && (adminSummary || adminDashboard) && ("
ins = """      {user?.role === 'buyer' && buyerDashboard && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <StatCard
            title="Open payment attention"
            value={buyerDashboard.pendingPayments ?? 0}
            icon={Package}
          />
          <StatCard
            title="In escrow (demo)"
            value={buyerDashboard.escrowHeldOrders ?? 0}
            icon={MessageSquare}
          />
        </div>
      )}

"""
if m not in t:
    raise SystemExit("admin marker not found for buyer insert")
t = t.replace(m, ins + m, 1)
p.write_text(t, "utf-8")
print("ok")
