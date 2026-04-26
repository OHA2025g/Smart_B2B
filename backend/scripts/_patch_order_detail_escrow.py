from pathlib import Path

p = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "pages" / "OrderDetail.jsx"
t = p.read_text(encoding="utf-8")
if "handlePayment" in t:
    print("skip - already has handlePayment")
    raise SystemExit(0)

# Add state after updating
t = t.replace(
    "  const [updating, setUpdating] = useState(false);\n  const toast = useToast();",
    "  const [updating, setUpdating] = useState(false);\n  const [paymentUpdating, setPaymentUpdating] = useState(false);\n  const toast = useToast();",
    1,
)
# Add handler after handleStatus block - find closing of handleStatus
needle = "    } catch {\n      toast.add('Update failed', 'error');\n    } finally {\n      setUpdating(false);\n    }\n  };\n\n"
if needle not in t:
    raise SystemExit("handleStatus block not found")
insert = """    } catch {
      toast.add('Update failed', 'error');
    } finally {
      setUpdating(false);
    }
  };

  const handlePayment = async (paymentStatus) => {
    setPaymentUpdating(true);
    try {
      await ordersApi.updatePayment(id, paymentStatus);
      const { data } = await ordersApi.getById(id);
      setOrder(data.data.order);
      const tr = await ordersApi.getTimeline(id);
      setTimeline(tr.data.data.timeline || []);
      toast.add('Payment status updated', 'success');
    } catch {
      toast.add('Update failed', 'error');
    } finally {
      setPaymentUpdating(false);
    }
  };

"""
t = t.replace(needle, insert, 1)

old = """      <div className="relative overflow-hidden rounded-3xl border border-slate-700/50 bg-slate-900 text-white shadow-2xl shadow-slate-900/25 print:hidden">
        <div className="absolute inset-0 bg-mesh-dark opacity-60" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-teal-500/15 rounded-full blur-3xl" />
        <div className="relative p-6 sm:p-8">
          <div className="flex items-start gap-4">
            <div className="rounded-2xl bg-white/10 p-3 ring-1 ring-white/20">
              <Shield className="h-8 w-8 text-teal-300" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-bold tracking-tight">Escrow &amp; secure settlement</h2>
                <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-200 ring-1 ring-amber-400/30">
                  Roadmap
                </span>
              </div>
              <p className="text-sm text-slate-300 mt-3 leading-relaxed max-w-2xl">
                Funds will be held in escrow until delivery confirmation?reducing counterparty risk for both sides.
                This card is a <span className="text-white font-medium">product-grade placeholder</span> for investor and
                mid-term demos; no payments are processed in this build.
              </p>
              <ul className="mt-4 grid sm:grid-cols-3 gap-3 text-xs text-slate-400">
                <li className="rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">Milestone release</li>
                <li className="rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">Dispute window</li>
                <li className="rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">Audit trail</li>
              </ul>
            </div>
          </div>
        </div>
      </div>"""

# File may have different quote character - use shorter unique start/end
start = "      <div className=\"relative overflow-hidden rounded-3xl"
end = "      {displayTimeline.length > 0 && ("
idx0 = t.find(start)
idx1 = t.find(end, idx0)
if idx0 < 0 or idx1 < 0:
    raise SystemExit("escrow block markers not found")

new_block = """      <Card className="print:hidden border-slate-200/90">
        <div className="px-5 py-4 border-b border-slate-100">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="section-title flex items-center gap-2">
              <Shield className="h-5 w-5 text-teal-600" />
              Escrow payment protection
            </h2>
            <Badge variant="primary">{(order.paymentStatus || 'payment_pending').replace(/_/g, ' ')}</Badge>
          </div>
          <p className="text-xs text-slate-500 mt-2 max-w-3xl">
            Communication is monitored to maintain buyer-seller trust. No real payment provider is connected—use the demo
            actions to walk through a typical release workflow.
          </p>
        </div>
        <ol className="p-5 sm:p-6 space-y-2 text-sm text-slate-700 list-decimal list-inside">
          <li>Buyer initiates payment</li>
          <li>SmartB2B holds amount securely (escrow)</li>
          <li>Seller ships goods (order status)</li>
          <li>Buyer confirms delivery</li>
          <li>Payment released to seller (or refunded if applicable)</li>
        </ol>
        <div className="px-5 pb-5 flex flex-wrap gap-2 print:hidden">
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('payment_pending')}
            variant="secondary"
          >
            1. Mark payment initiated
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('escrow_held')}
            variant="secondary"
          >
            2. Mark escrow held
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('released')}
            variant="primary"
          >
            3. Mark released
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={paymentUpdating}
            onClick={() => handlePayment('refunded')}
            variant="ghost"
            className="text-amber-700"
          >
            Mark refunded
          </Button>
        </div>
      </Card>

"""

t = t[:idx0] + new_block + "\n\n" + t[idx1:]
p.write_text(t, encoding="utf-8")
print("OrderDetail escrow block replaced")
