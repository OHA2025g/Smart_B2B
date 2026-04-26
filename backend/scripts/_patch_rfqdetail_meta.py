from pathlib import Path

p = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "pages" / "RFQDetail.jsx"
t = p.read_text(encoding="utf-8")
if "Delivery location" in t and "rfq.deliveryLocation" in t:
    print("skip")
    raise SystemExit(0)
old = """      <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40">
        <div className="p-5 sm:p-6 grid sm:grid-cols-2 lg:grid-cols-4 gap-5 text-sm">
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Created</p>
            <p className="font-semibold text-slate-900">{rfq.createdAt ? new Date(rfq.createdAt).toLocaleString() : '—'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Valid until</p>
            <p className="font-semibold text-slate-900">{rfq.validUntil ? new Date(rfq.validUntil).toLocaleDateString() : '—'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Line items</p>
            <p className="font-semibold text-slate-900">{rfq.items?.length ?? 0}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4 min-w-0">
            <p className="section-heading mb-1">RFQ ID</p>
            <p className="font-mono text-xs text-slate-700 truncate">{rfq._id}</p>
          </div>
        </div>
      </Card>"""

# File may have wrong dash character for em dash
if old not in t:
    # try with replacement char
    for rep in ("\\u2014", "�?"):
        test = old.replace("'—'", "'" + rep + "'")
        if test in t:
            old = test
            break
    else:
        raise SystemExit("meta card block not found")

new = """      <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40">
        <div className="p-5 sm:p-6 grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 text-sm">
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Created</p>
            <p className="font-semibold text-slate-900">{rfq.createdAt ? new Date(rfq.createdAt).toLocaleString() : 'N/A'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Valid until</p>
            <p className="font-semibold text-slate-900">{rfq.validUntil ? new Date(rfq.validUntil).toLocaleDateString() : 'N/A'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Required by</p>
            <p className="font-semibold text-slate-900">
              {rfq.requiredByDate ? new Date(rfq.requiredByDate).toLocaleDateString() : 'N/A'}
            </p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Priority</p>
            <p className="font-semibold text-slate-900 capitalize">{rfq.priority || 'normal'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4 sm:col-span-2">
            <p className="section-heading mb-1">Delivery location</p>
            <p className="font-semibold text-slate-900 break-words">{rfq.deliveryLocation || 'N/A'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Line items</p>
            <p className="font-semibold text-slate-900">{rfq.items?.length ?? 0}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4 min-w-0">
            <p className="section-heading mb-1">RFQ ID</p>
            <p className="font-mono text-xs text-slate-700 truncate">{rfq._id}</p>
          </div>
        </div>
        {rfq.buyerNotes ? (
          <div className="px-5 sm:px-6 pb-5">
            <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Buyer notes</p>
            <p className="text-sm text-slate-800 whitespace-pre-wrap border border-slate-100 rounded-xl p-3 bg-white">{rfq.buyerNotes}</p>
          </div>
        ) : null}
        <p className="px-5 sm:px-6 pb-4 text-xs text-amber-800/90 bg-amber-50/60 border-t border-amber-100/80 py-2">
          Communication is monitored to maintain buyer-seller trust and platform safety.
        </p>
      </Card>"""
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("RFQDetail meta ok")
