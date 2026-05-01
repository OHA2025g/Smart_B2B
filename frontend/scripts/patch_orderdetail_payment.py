from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "OrderDetail.jsx"
t = p.read_text("utf-8")
if "OrderPaymentPanel" in t:
    print("skip")
    raise SystemExit(0)

t = t.replace(
    "import { Badge } from '../components/ui/Badge';\nimport { Button } from '../components/ui/Button';\n",
    "import { Badge } from '../components/ui/Badge';\nimport { Button } from '../components/ui/Button';\nimport { OrderPaymentPanel } from '../components/OrderPaymentPanel';\nimport { paymentStatusLabel } from '../components/SupplierPlanBadges';\n",
    1,
)

t = t.replace(
    """            <p className="text-xs leading-relaxed">
              On-platform escrow and milestone releases are not active in this demo build. Settlement terms follow your
              negotiated quote and offline arrangements.
            </p>""",
    """            <p className="text-xs leading-relaxed">
              This document references the agreed commercial terms. Optional on-platform <strong>demo escrow</strong> (see
              the order page) simulates hold and release for evaluation only; no real funds move.
            </p>""",
    1,
)

start = t.find('      <Card className="print:hidden border-slate-200/90">\n        <div className="px-5 py-4 border-b border-slate-100">\n          <div className="flex items-center justify-between flex-wrap gap-2">\n            <h2 className="section-title flex items-center gap-2">\n              <Shield className="h-5 w-5 text-teal-600" />\n              Escrow payment protection')
if start == -1:
    raise SystemExit("escrow card header not found")

end_marker = "\n\n\n      {displayTimeline.length"
end = t.find(end_marker, start)
if end == -1:
    end_marker2 = "      {displayTimeline.length"
    end = t.find(end_marker2, start)
    if end == -1:
        raise SystemExit("end marker not found")

new_block = r"""      <div className="print:hidden max-w-4xl">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 uppercase">Payment status</span>
          <Badge variant="primary" className="text-xs">
            {paymentStatusLabel(order.paymentStatus || 'payment_pending')}
          </Badge>
        </div>
        <OrderPaymentPanel
          order={order}
          orderId={id}
          user={user}
          onOrderUpdate={(o) => {
            setOrder(o);
            ordersApi.getTimeline(id).then((r) => setTimeline(r.data.data.timeline || [])).catch(() => {});
          }}
        />
      </div>
"""

t = t[:start] + new_block + t[end:]
p.write_text(t, "utf-8")
print("ok")
