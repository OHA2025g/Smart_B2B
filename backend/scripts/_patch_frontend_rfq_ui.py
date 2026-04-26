"""Patch RFQDetail.jsx, SellerRFQs.jsx, client.js for quote UX and reject API."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (SmartB2B)
FD = ROOT / "frontend/src/pages/RFQDetail.jsx"
SF = ROOT / "frontend/src/pages/SellerRFQs.jsx"
CJ = ROOT / "frontend/src/api/client.js"


def patch_client():
    t = CJ.read_text(encoding="utf-8")
    if "rejectQuote" in t:
        print("client.js skip")
        return
    needle = "  acceptQuote: (rfqId, quoteId) => client.post(`${apiBase}/api/rfq/${rfqId}/accept-quote/${quoteId}`),\n"
    add = needle + "  rejectQuote: (rfqId, quoteId) => client.post(`${apiBase}/api/rfq/${rfqId}/reject-quote/${quoteId}`),\n"
    if needle not in t:
        raise SystemExit("client acceptQuote line not found")
    CJ.write_text(t.replace(needle, add, 1), encoding="utf-8")
    print("client.js: rejectQuote")


def patch_seller_rfqs():
    t = SF.read_text(encoding="utf-8")
    old_val_end = "    setFieldErrors(err);\n    return Object.keys(err).length === 0;\n  };"
    new_val_end = "    setFieldErrors(err);\n    const ok = Object.keys(err).length === 0;\n    return { ok, err };\n  };"
    if "return { ok, err };" in t:
        print("SellerRFQs validate skip")
    else:
        if old_val_end not in t:
            raise SystemExit("SellerRFQs validate end not found")
        t = t.replace(old_val_end, new_val_end, 1)

    old_hs = """  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!modalRfq || !validate()) {
      toast.add('Please fix the highlighted fields.', 'error');
      return;
    }
"""
    new_hs = """  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!modalRfq) return;
    const { ok, err } = validate();
    if (!ok) {
      const msgs = Object.values(err).filter(Boolean);
      toast.add(msgs.length ? msgs.join(' · ') : 'Please fix the highlighted fields.', 'error');
      return;
    }
"""
    if "if (!modalRfq) return;" in t and "const { ok, err } = validate();" in t:
        print("SellerRFQs handleSubmit skip")
    else:
        if old_hs not in t:
            raise SystemExit("SellerRFQs handleSubmit not found")
        t = t.replace(old_hs, new_hs, 1)

    SF.write_text(t, encoding="utf-8")
    print("SellerRFQs.jsx patched")


def patch_rfq_detail():
    t = FD.read_text(encoding="utf-8")
    if "function entityIdStr" in t:
        print("RFQDetail already patched")
        return

    inject = """
function entityIdStr(ref) {
  if (ref == null) return '';
  if (typeof ref === 'string') return ref;
  return (ref.id || ref._id)?.toString?.() || '';
}

function quoteIdStr(q) {
  if (!q) return '';
  return entityIdStr(q._id || q.id || q);
}

"""
    t = t.replace(
        "import { useState, useEffect, useMemo } from 'react';\n",
        "import { useState, useEffect, useMemo } from 'react';\nimport { Link } from 'react-router-dom';\n",
    )
    t = t.replace(
        "import { Send, CheckCircle, Clock, MessageSquare, Trophy, AlertTriangle } from 'lucide-react';\n",
        inject + "import { Send, CheckCircle, Clock, MessageSquare, Trophy, AlertTriangle, XCircle, ExternalLink, Printer } from 'lucide-react';\n",
    )

    t = t.replace(
        "    const buyerIdStr = rfq.buyerId?._id?.toString() || rfq.buyerId?.toString();\n"
        "    const isRfqBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;\n",
        "    const buyerIdStr = entityIdStr(rfq.buyerId);\n"
        "    const isRfqBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;\n",
    )
    t = t.replace(
        "          const buyerStr = next.buyerId?._id?.toString() || next.buyerId?.toString();\n"
        "          const isRfqBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerStr;\n",
        "          const buyerStr = entityIdStr(next.buyerId);\n"
        "          const isRfqBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerStr;\n",
    )
    t = t.replace(
        "  const buyerIdStr = rfq.buyerId?._id?.toString() || rfq.buyerId?.toString();\n"
        "  const isBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;\n",
        "  const buyerIdStr = entityIdStr(rfq.buyerId);\n"
        "  const isBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;\n",
    )

    old_memo = """      return row
        ? {
            company: row.company_name || row.seller_name,
            price: row.quoted_price,
            delivery: row.delivery_days,
            trust: row.trust_score,
            score: row.quote_score,
          }
        : null;
"""
    new_memo = """      return row
        ? {
            company: (row.company_name || '').trim() || row.seller_name || 'Supplier',
            price: row.quoted_price,
            delivery: row.delivery_days,
            trust: row.trust_score,
            score: row.quote_score,
            why: `Ranked #${row.rank || 1} by quote score for this RFQ (price, delivery, trust).`,
          }
        : null;
"""
    if old_memo in t:
        t = t.replace(old_memo, new_memo, 1)

    old_fallback = """    return {
      company: q.sellerId?.name,
      price: tp,
      delivery: Math.round(avgDel),
      trust: q.sellerId?.trustScore,
      score: q.quoteScore,
    };
"""
    new_fallback = """    return {
      company: q.sellerId?.name || 'Supplier',
      price: tp,
      delivery: Math.round(avgDel),
      trust: q.sellerId?.trustScore,
      score: q.quoteScore,
      why: 'Top quote by score among responses on this RFQ.',
    };
"""
    if old_fallback in t:
        t = t.replace(old_fallback, new_fallback, 1)

    t = t.replace(
        "                    <span className=\"font-semibold text-slate-800\">Why:</span> Best balance of price, delivery speed, and supplier\n                    trust score.\n",
        "                    <span className=\"font-semibold text-slate-800\">Why:</span> {recommended.why}\n",
    )

    reject_block = """
  const handleRejectQuote = async (quoteId) => {
    if (!quoteId || !window.confirm('Reject this quote? You can still accept another offer.')) return;
    setAccepting(quoteId);
    try {
      await rfqApi.rejectQuote(id, quoteId);
      toast.add('Quote rejected.', 'success');
      const r0 = await rfqApi.getById(id);
      setRfq(r0.data.data.rfq);
      const r1 = await rfqApi.getQuotes(id);
      setQuotes(r1.data.data.quotes || []);
      try {
        const r2 = await rfqApi.getQuoteComparison(id);
        setComparison(r2.data.data.comparison || []);
      } catch {
        setComparison([]);
      }
      const r3 = await rfqApi.getTimeline(id);
      setTimeline(r3.data.data.timeline || []);
    } catch (e) {
      const d = e.response?.data?.detail;
      toast.add((typeof d === 'object' && d?.message) || e.response?.data?.message || 'Failed to reject quote', 'error');
    } finally {
      setAccepting(null);
    }
  };

"""
    t = t.replace(
        "  const handleAcceptQuote = async (quoteId) => {\n",
        reject_block + "  const handleAcceptQuote = async (quoteId) => {\n",
        1,
    )

    old_row = """                ).map((row, idx) => {
                  const quoteId = row.quoteId || quotes[idx]?._id;
                  const quoteStatus = quotes.find((q) => q._id === quoteId)?.status ?? row.status;
"""
    new_row = """                ).map((row, idx) => {
                  const sid = (row.seller_id || '').toString();
                  const byQuoteId = row.quoteId ? quotes.find((q) => quoteIdStr(q) === String(row.quoteId)) : null;
                  const bySeller = sid ? quotes.find((q) => (q.sellerId?.id || q.sellerId?._id || q.sellerId)?.toString() === sid) : null;
                  const quoteMeta = byQuoteId || bySeller || quotes[idx];
                  const quoteId = String(row.quoteId || quoteIdStr(quoteMeta) || '');
                  const quoteStatus = quoteMeta?.status ?? row.status;
"""
    if old_row not in t:
        raise SystemExit("RFQDetail map row block not found")
    t = t.replace(old_row, new_row, 1)

    t = t.replace(
        "                  const expired = row.is_expired || quotes.find((q) => q._id === quoteId)?.isQuoteExpired;\n",
        "                  const expired = row.is_expired || quoteMeta?.isQuoteExpired;\n",
    )

    t = t.replace(
        "                        <span className=\"block\">{row.seller_name}</span>\n",
        "                        <span className=\"block\">{(row.company_name || '').trim() || row.seller_name || '—'}</span>\n",
    )

    old_action = """                        ) : !rejected && rfq.status !== 'accepted' && quoteId && !expired ? (
                          <Button size=\"sm\" className=\"rounded-lg shadow-sm\" onClick={() => handleAcceptQuote(quoteId)} disabled={!!accepting}>
                            <CheckCircle className=\"h-4 w-4 mr-1\" /> Accept
                          </Button>
                        ) : expired ? (
"""
    new_action = """                        ) : !rejected && rfq.status !== 'accepted' && quoteId && !expired ? (
                          <div className=\"flex flex-wrap gap-2\">
                            <Button size=\"sm\" className=\"rounded-lg shadow-sm\" onClick={() => handleAcceptQuote(quoteId)} disabled={!!accepting}>
                              <CheckCircle className=\"h-4 w-4 mr-1\" /> Accept
                            </Button>
                            <Button type=\"button\" variant=\"secondary\" size=\"sm\" className=\"rounded-lg\" onClick={() => handleRejectQuote(quoteId)} disabled={!!accepting}>
                              <XCircle className=\"h-4 w-4 mr-1\" /> Reject
                            </Button>
                          </div>
                        ) : expired ? (
"""
    if old_action not in t:
        raise SystemExit("RFQDetail action block not found")
    t = t.replace(old_action, new_action, 1)

    old_accepted = """                        {accepted ? (
                          <Badge variant=\"success\" className=\"font-semibold\">
                            Accepted
                          </Badge>
                        ) : !rejected && rfq.status !== 'accepted' && quoteId && !expired ? (
"""
    new_accepted = """                        {accepted ? (
                          <div className=\"flex flex-col gap-2 items-start\">
                            <Badge variant=\"success\" className=\"font-semibold\">
                              Accepted
                            </Badge>
                            {rfq.linkedOrderId ? (
                              <div className=\"flex flex-wrap gap-2\">
                                <Link to={`/orders/${rfq.linkedOrderId}`}>
                                  <Button type=\"button\" size=\"sm\" variant=\"secondary\" className=\"rounded-lg gap-1\">
                                    <ExternalLink className=\"h-4 w-4\" /> Open order
                                  </Button>
                                </Link>
                                <Link to={`/orders/${rfq.linkedOrderId}`} target=\"_blank\" rel=\"noreferrer\">
                                  <Button type=\"button\" size=\"sm\" className=\"rounded-lg gap-1\">
                                    <Printer className=\"h-4 w-4\" /> Print / PO
                                  </Button>
                                </Link>
                              </div>
                            ) : (
                              <Link to=\"/orders\">
                                <Button type=\"button\" size=\"sm\" variant=\"secondary\" className=\"rounded-lg\">
                                  View orders
                                </Button>
                              </Link>
                            )}
                          </div>
                        ) : !rejected && rfq.status !== 'accepted' && quoteId && !expired ? (
"""
    if old_accepted not in t:
        raise SystemExit("RFQDetail accepted block not found")
    t = t.replace(old_accepted, new_accepted, 1)

    FD.write_text(t, encoding="utf-8")
    print("RFQDetail.jsx patched")


if __name__ == "__main__":
    patch_client()
    patch_seller_rfqs()
    patch_rfq_detail()
