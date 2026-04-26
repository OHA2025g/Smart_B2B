import { useState, useEffect, useMemo, useRef, Fragment } from 'react';
import { Link, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';

function entityIdStr(ref) {
  if (ref == null) return '';
  if (typeof ref === 'string') return ref;
  return (ref.id || ref._id)?.toString?.() || '';
}

function quoteIdStr(q) {
  if (!q) return '';
  return entityIdStr(q._id || q.id || q);
}

function lineItemLabel(it) {
  if (!it) return '—';
  const p = it.productId;
  if (p && typeof p === 'object' && p.title) return p.title;
  if (p && typeof p === 'string') return p;
  return 'Product';
}

function rfqQtyByProductId(rfq) {
  const m = new Map();
  (rfq?.items || []).forEach((line) => {
    const id = entityIdStr(line?.productId?._id || line?.productId);
    if (id) m.set(id, line?.quantity);
  });
  return m;
}

import { Send, CheckCircle, Clock, MessageSquare, Trophy, AlertTriangle, XCircle, ExternalLink, Printer, ChevronDown, ChevronUp, ArrowLeftRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { rfqApi, messagesApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { formatDateTimeIst, formatDateIst } from '../lib/istTime';

export default function RFQDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [rfq, setRfq] = useState(null);
  const [quotes, setQuotes] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [thread, setThread] = useState(null);
  const [messageText, setMessageText] = useState('');
  const [moderationConfirmOpen, setModerationConfirmOpen] = useState(false);
  const [composerBlockedHighlight, setComposerBlockedHighlight] = useState(false);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(null);
  /** quoteId string -> boolean: expanded line-item + terms view */
  const [openDetailIds, setOpenDetailIds] = useState({});
  const [counterOffers, setCounterOffers] = useState([]);
  const [counterOpen, setCounterOpen] = useState(null);
  const [counterText, setCounterText] = useState('');
  const [counterTotal, setCounterTotal] = useState('');
  const [postingCounter, setPostingCounter] = useState(false);
  const didAutoExpandRef = useRef(false);
  const toast = useToast();

  useEffect(() => {
    rfqApi
      .getById(id)
      .then((res) => setRfq(res.data.data.rfq))
      .catch(() => setRfq(null))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!rfq || !user) return;
    rfqApi.getQuotes(id).then((res) => setQuotes(res.data.data.quotes || [])).catch(() => setQuotes([]));
    const buyerIdStr = entityIdStr(rfq.buyerId);
    const isRfqBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;
    if (isRfqBuyer) {
      rfqApi.getQuoteComparison(id).then((res) => setComparison(res.data.data.comparison || [])).catch(() => setComparison([]));
    } else {
      setComparison([]);
    }
    rfqApi.getTimeline(id).then((res) => setTimeline(res.data.data.timeline || [])).catch(() => setTimeline([]));
    messagesApi.get(id).then((res) => setThread(res.data.data.thread)).catch(() => setThread(null));
    rfqApi.getCounterOffers(id).then((res) => setCounterOffers(res.data.data.counterOffers || [])).catch(() => setCounterOffers([]));
  }, [rfq, id, user]);

  useEffect(() => {
    const onRfqUpdated = (e) => {
      if (!id || e.detail?.rfqId !== id) return;
      rfqApi
        .getById(id)
        .then((res) => {
          const next = res.data.data.rfq;
          setRfq(next);
          const buyerStr = entityIdStr(next.buyerId);
          const isRfqBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerStr;
          return rfqApi.getQuotes(id).then((r2) => {
            setQuotes(r2.data.data.quotes || []);
            if (isRfqBuyer) {
              return rfqApi.getQuoteComparison(id).then((r3) => setComparison(r3.data.data.comparison || []));
            }
            return null;
          });
        })
        .catch(() => {});
      rfqApi.getTimeline(id).then((res) => setTimeline(res.data.data.timeline || [])).catch(() => {});
      rfqApi.getCounterOffers(id).then((res) => setCounterOffers(res.data.data.counterOffers || [])).catch(() => setCounterOffers([]));
    };
    window.addEventListener('smartb2b:rfq-updated', onRfqUpdated);
    return () => window.removeEventListener('smartb2b:rfq-updated', onRfqUpdated);
  }, [id, user]);

  useEffect(() => {
    didAutoExpandRef.current = false;
  }, [id]);

  const rfqLineQty = useMemo(() => rfqQtyByProductId(rfq), [rfq]);

  /** On first load, expand the best-ranked quote so line-level pricing is visible without an extra click. */
  useEffect(() => {
    if (didAutoExpandRef.current || !quotes.length) return;
    const best = comparison.length ? comparison.find((r) => r.rank === 1) || comparison[0] : null;
    const idStr = best?.quoteId
      ? String(best.quoteId)
      : (() => {
          const sorted = [...quotes].sort((a, b) => (b.quoteScore || 0) - (a.quoteScore || 0));
          return quoteIdStr(sorted[0]);
        })();
    if (idStr) {
      setOpenDetailIds((o) => ({ ...o, [idStr]: true }));
      didAutoExpandRef.current = true;
    }
  }, [comparison, quotes, id]);

  const recommended = useMemo(() => {
    if (!rfq) return null;
    if (comparison.length) {
      const row = comparison.find((r) => r.rank === 1) || comparison[0];
      return row
        ? {
            company: (row.company_name || '').trim() || row.seller_name || 'Supplier',
            price: row.quoted_price,
            delivery: row.delivery_days,
            trust: row.trust_score,
            score: row.quote_score,
            why: `Ranked #${row.rank || 1} by quote score for this RFQ (price, delivery, trust).`,
          }
        : null;
    }
    if (!quotes.length) return null;
    const sorted = [...quotes].sort((a, b) => (b.quoteScore || 0) - (a.quoteScore || 0));
    const q = sorted[0];
    const tp = q.items?.reduce((s, i) => s + (i.unitPrice || 0) * (i.availableQty || 0), 0) || 0;
    const avgDel = q.items?.length
      ? q.items.reduce((s, i) => s + (Number(i.deliveryDays) || 7), 0) / q.items.length
      : 7;
    return {
      company: q.sellerId?.name || 'Supplier',
      price: tp,
      delivery: Math.round(avgDel),
      trust: q.sellerId?.trustScore,
      score: q.quoteScore,
      why: 'Top quote by score among responses on this RFQ.',
    };
  }, [rfq, comparison, quotes]);

  const sendChatMessage = async (text, confirmSend = false) => {
    const trimmed = (text || '').trim();
    if (!trimmed) return;
    try {
      const { data } = await messagesApi.post(id, trimmed, { confirmSend });
      setThread(data.data.thread);
      setModerationConfirmOpen(false);
      setComposerBlockedHighlight(false);
      const msgs = data.data.thread?.messages || [];
      const last = msgs[msgs.length - 1];
      if (last?.moderationFlag || last?.containsContactAttempt) {
        toast.add('Message sent for admin review.', 'success');
      } else {
        toast.add('Message sent', 'success');
      }
      setMessageText('');
    } catch (e) {
      const st = e.response?.status;
      const detail = e.response?.data?.detail;
      const code = typeof detail === 'object' && detail ? detail.code : null;
      if (st === 422 && code === 'CONTACT_SHARING_BLOCKED') {
        setComposerBlockedHighlight(true);
        toast.add(
          'Direct contact sharing is restricted. Please continue communication inside B2Bभारत.',
          'error',
        );
        return;
      }
      if (st === 409 && code === 'MODERATION_CONFIRM_REQUIRED') {
        setModerationConfirmOpen(true);
        return;
      }
      const msg =
        (typeof detail === 'object' && detail?.message) ||
        (typeof detail === 'string' ? detail : null) ||
        'Failed to send message';
      toast.add(msg, 'error');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    await sendChatMessage(messageText, false);
  };

  const handleConfirmModerationSend = async () => {
    await sendChatMessage(messageText, true);
  };


  const handlePostCounter = async (e) => {
    e?.preventDefault?.();
    if (!counterOpen) return;
    const msg = (counterText || '').trim();
    if (!msg) {
      toast.add('Describe your counter-offer for the supplier.', 'error');
      return;
    }
    let proposedTotal;
    if ((counterTotal || '').trim() !== '') {
      const n = parseFloat(String(counterTotal).replace(/,/g, ''));
      if (Number.isNaN(n) || n < 0) {
        toast.add('Target total must be a valid non-negative number.', 'error');
        return;
      }
      proposedTotal = n;
    }
    setPostingCounter(true);
    try {
      const payload = { quoteId: counterOpen, message: msg };
      if (proposedTotal !== undefined) payload.proposedTotal = proposedTotal;
      await rfqApi.postCounterOffer(id, payload);
      toast.add('Counter-offer sent. The supplier can reply with a revised quote.', 'success');
      setCounterOpen(null);
      setCounterText('');
      setCounterTotal('');
      const r = await rfqApi.getCounterOffers(id);
      setCounterOffers(r.data.data.counterOffers || []);
    } catch (err) {
      const d = err.response?.data?.detail;
      const code = typeof d === 'object' && d ? d.code : null;
      if (err.response?.status === 400 && (code === 'VALIDATION_ERROR' || typeof d === 'object')) {
        toast.add((d && d.message) || 'Could not send counter-offer. Is the RFQ still open?', 'error');
      } else {
        const msg0 =
          (typeof d === 'object' && d?.message) ||
          err.response?.data?.message ||
          'Failed to send counter-offer';
        toast.add(msg0, 'error');
      }
    } finally {
      setPostingCounter(false);
    }
  };

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

  const handleAcceptQuote = async (quoteId) => {
    setAccepting(quoteId);
    try {
      await rfqApi.acceptQuote(id, quoteId);
      toast.add('Quote accepted. Order created.', 'success');
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
      toast.add((typeof d === 'object' && d?.message) || e.response?.data?.message || 'Failed to accept quote', 'error');
    } finally {
      setAccepting(null);
    }
  };

  if (loading || !rfq) {
    return (
      <div className="space-y-4 max-w-5xl">
        <div className="h-10 w-64 bg-slate-200 rounded-xl animate-pulse" />
        <div className="h-32 bg-slate-100 rounded-2xl animate-pulse" />
        <div className="h-48 bg-slate-100 rounded-2xl animate-pulse" />
      </div>
    );
  }

  const buyerIdStr = entityIdStr(rfq.buyerId);
  const isBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;

  const steps = [
    { key: 'sent', label: 'RFQ Created', sub: 'Posted to suppliers' },
    { key: 'quoted', label: 'Quoted', sub: 'Responses received' },
    { key: 'accepted', label: 'Accepted', sub: 'Awarded to supplier' },
    { key: 'closed', label: 'Closed', sub: 'Completed or archived' },
  ];
  const rfqStepIndex = (status) => {
    if (status === 'rejected') return 3;
    const order = ['sent', 'quoted', 'accepted', 'closed'];
    const i = order.indexOf(status);
    return i >= 0 ? i : 0;
  };
  const stepIndex = rfqStepIndex(rfq.status);

  const uid = user?.id?.toString() || user?._id?.toString();

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <p className="section-heading mb-1">Request for quote</p>
          <h1 className="page-heading">RFQ #{rfq._id.slice(-6)}</h1>
          <p className="text-sm text-slate-500 mt-1">Structured procurement thread with ranked quotes and on-platform messaging.</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          {rfq.isExpired && (
            <Badge variant="danger" className="gap-1 font-semibold px-3 py-1">
              <AlertTriangle className="h-3.5 w-3.5" /> Expired
            </Badge>
          )}
          <Badge
            variant={rfq.status === 'accepted' ? 'success' : rfq.status === 'closed' || rfq.status === 'rejected' ? 'danger' : 'warning'}
            className="font-semibold px-3 py-1 capitalize"
          >
            {rfq.status}
          </Badge>
        </div>
      </div>

      <Card className="border-slate-200/90 shadow-lg shadow-slate-200/40">
        <div className="p-5 sm:p-6 grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 text-sm">
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Created</p>
            <p className="font-semibold text-slate-900">{rfq.createdAt ? formatDateTimeIst(rfq.createdAt) : 'N/A'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Valid until</p>
            <p className="font-semibold text-slate-900">{rfq.validUntil ? formatDateIst(rfq.validUntil) : 'N/A'}</p>
          </div>
          <div className="rounded-xl bg-slate-50/80 border border-slate-100 p-4">
            <p className="section-heading mb-1">Required by</p>
            <p className="font-semibold text-slate-900">
              {rfq.requiredByDate ? formatDateIst(rfq.requiredByDate) : 'N/A'}
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
      </Card>

      {/* Stepper */}
      <Card className="border-slate-200/90 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-teal-50/50 to-white">
          <h2 className="section-title">Progress</h2>
          <p className="text-sm text-slate-500 mt-0.5">Where this RFQ sits in the quote-to-order lifecycle.</p>
        </div>
        <div className="p-5 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-start gap-6 sm:gap-0">
            {steps.map((step, i) => {
              const done = i <= stepIndex;
              const active = i === stepIndex;
              return (
                <div key={step.key} className="flex sm:flex-1 items-start gap-3 sm:flex-col sm:items-center sm:text-center min-w-0">
                  <div className="flex sm:w-full sm:items-center gap-0 sm:gap-0">
                    <div
                      className={`flex h-12 w-12 shrink-0 rounded-full items-center justify-center text-sm font-bold transition-all ${
                        done
                          ? 'bg-teal-600 text-white shadow-lg shadow-teal-600/30'
                          : 'bg-slate-100 text-slate-400 ring-2 ring-slate-200'
                      } ${active ? 'ring-4 ring-teal-200' : ''}`}
                    >
                      {i + 1}
                    </div>
                    {i < steps.length - 1 && (
                      <div
                        className={`hidden sm:block flex-1 h-1 mx-2 rounded-full mt-[22px] -mb-1 ${i < stepIndex ? 'bg-teal-400' : 'bg-slate-200'}`}
                        aria-hidden
                      />
                    )}
                  </div>
                  <div className="pt-0.5 sm:pt-4 sm:px-1">
                    <p className={`font-bold text-sm ${done ? 'text-slate-900' : 'text-slate-400'}`}>{step.label}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{step.sub}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Timeline / Activity */}
      {timeline.length > 0 && (
        <Card className="border-slate-200/90">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="section-title flex items-center gap-2">
              <Clock className="h-5 w-5 text-teal-600" /> Recent activity
            </h2>
            <p className="text-sm text-slate-500 mt-1">Audit-style events for this RFQ.</p>
          </div>
          <div className="p-5 sm:p-6">
            <ul className="space-y-0">
              {timeline.map((e, idx) => (
                <li key={e._id || e.id} className="flex gap-4 relative">
                  {idx < timeline.length - 1 && <span className="absolute left-[7px] top-8 bottom-0 w-px bg-slate-200" aria-hidden />}
                  <span className="mt-1.5 h-3.5 w-3.5 rounded-full bg-teal-500 ring-4 ring-teal-100 shrink-0 z-10" />
                  <div className="pb-6 flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-400 tabular-nums">
                      {e.created_at ? formatDateTimeIst(e.created_at) : ''}
                    </p>
                    <p className="font-semibold text-slate-900 mt-1">{e.event_label}</p>
                    <Badge variant="outline" className="mt-2 text-[10px]">
                      {e.actor_role}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      )}

      <Card className="border-slate-200/90">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="section-title">Requested items</h2>
        </div>
        <ul className="divide-y divide-slate-100">
          {rfq.items?.map((item, i) => (
            <li key={i} className="flex flex-wrap justify-between gap-2 px-5 py-4 text-sm">
              <span className="font-medium text-slate-800">{item.productId?.title || item.productId}</span>
              <span className="text-slate-500 font-medium tabular-nums">Qty {item.quantity}</span>
            </li>
          ))}
        </ul>
      </Card>

      {isBuyer && (comparison.length > 0 || quotes.length > 0) && (
        <Card className="border-slate-200/90 shadow-xl shadow-slate-200/30 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-900 to-slate-800 text-white">
            <h2 className="text-lg font-bold tracking-tight flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-400" /> Quote comparison
            </h2>
            <p className="text-sm text-slate-300 mt-1">Ranked offers — the best row is highlighted for faster decisions.</p>
          </div>
          {recommended && (
            <div className="p-5 sm:p-6 border-b border-teal-100/80 bg-gradient-to-br from-teal-50 via-white to-slate-50">
              <p className="text-xs font-bold uppercase tracking-wider text-teal-800 mb-2">Recommended supplier</p>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-lg font-bold text-slate-900">{recommended.company || '—'}</p>
                  <p className="text-sm text-slate-600 mt-2 max-w-xl">
                    <span className="font-semibold text-slate-800">Why:</span> {recommended.why}
                  </p>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div className="rounded-xl bg-white/90 border border-slate-200/80 px-3 py-2 shadow-sm">
                    <p className="text-[10px] font-semibold uppercase text-slate-500">Quoted</p>
                    <p className="font-bold text-teal-700 tabular-nums">₹{Number(recommended.price || 0).toLocaleString()}</p>
                  </div>
                  <div className="rounded-xl bg-white/90 border border-slate-200/80 px-3 py-2 shadow-sm">
                    <p className="text-[10px] font-semibold uppercase text-slate-500">Delivery</p>
                    <p className="font-bold text-slate-900">{recommended.delivery ?? '—'} days</p>
                  </div>
                  <div className="rounded-xl bg-white/90 border border-slate-200/80 px-3 py-2 shadow-sm">
                    <p className="text-[10px] font-semibold uppercase text-slate-500">Trust</p>
                    <p className="font-bold text-slate-900">{recommended.trust != null ? `${Math.round(Number(recommended.trust))}%` : '—'}</p>
                  </div>
                  <div className="rounded-xl bg-white/90 border border-slate-200/80 px-3 py-2 shadow-sm">
                    <p className="text-[10px] font-semibold uppercase text-slate-500">Score</p>
                    <p className="font-bold text-slate-900">{recommended.score != null ? recommended.score : '—'}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          <p className="px-4 sm:px-5 py-2.5 text-xs sm:text-sm text-slate-600 border-b border-slate-100 bg-slate-50/90">
            Use the arrow beside each rank to open the full offer: <span className="font-semibold text-slate-800">line-item unit prices, quantities, per-line delivery, notes, seller message, and terms</span> (revised offers include the same fields as the current version).
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Rank</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Seller</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Price</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Delivery</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Avail.</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Trust</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Score</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Valid</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Status</th>
                  <th className="py-3 px-4 font-semibold whitespace-nowrap">Action</th>
                </tr>
              </thead>
              <tbody>
                {(comparison.length > 0
                  ? comparison
                  : quotes.map((q) => ({
                      quoteId: q._id,
                      seller_name: q.sellerId?.name,
                      verified_supplier: !!q.sellerId?.isVerifiedSupplier,
                      trust_score: q.sellerId?.trustScore,
                      quoted_price: q.items?.reduce((s, i) => s + (i.unitPrice || 0) * (i.availableQty || 0), 0) || 0,
                      delivery_days: q.items?.[0]?.deliveryDays ?? '—',
                      available_qty: q.items?.[0]?.availableQty ?? '—',
                      quote_score: q.quoteScore,
                      rank: 0,
                      status: q.status,
                      quote_valid_until: q.quoteValidUntil,
                      is_expired: q.isQuoteExpired,
                      best_quote: false,
                    }))
                ).map((row, idx) => {
                  const sid = (row.seller_id || '').toString();
                  const byQuoteId = row.quoteId
                    ? quotes.find((q) => quoteIdStr(q) === String(row.quoteId))
                    : null;
                  const bySeller = sid
                    ? quotes.find((q) => (q.sellerId?.id || q.sellerId?._id || q.sellerId)?.toString() === sid)
                    : null;
                  const quoteMeta = byQuoteId || bySeller || quotes[idx];
                  const quoteId = String(row.quoteId || quoteIdStr(quoteMeta) || '');
                  const quoteStatus = quoteMeta?.status ?? row.status;
                  const accepted = quoteStatus === 'accepted';
                  const rejected = quoteStatus === 'rejected';
                  const isBest = row.best_quote || (comparison.length > 0 && row.rank === 1);
                  const expired = row.is_expired || quoteMeta?.isQuoteExpired;
                  const detailOpen = quoteId && openDetailIds[quoteId];
                  const lineItems = quoteMeta?.items || [];
                  const fmtInr = (n) =>
                    `₹${Number(n ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
                  return (
                    <Fragment key={quoteId || `row-${idx}`}>
                    <tr
                      className={`border-b border-slate-100 transition-colors ${
                        isBest
                          ? 'bg-gradient-to-r from-teal-50 via-emerald-50/80 to-teal-50/40 shadow-[inset_4px_0_0_0_rgb(13_148_136)]'
                          : idx % 2 === 1
                            ? 'bg-slate-50/40'
                            : 'bg-white'
                      }`}
                    >
                      <td className="py-4 px-4 align-top">
                        <div className="flex flex-wrap items-center gap-2">
                          {quoteId ? (
                            <button
                              type="button"
                              onClick={() => setOpenDetailIds((o) => ({ ...o, [quoteId]: !o[quoteId] }))}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:text-teal-800 shrink-0"
                              title={detailOpen ? 'Hide line items and terms' : 'Show line items and terms'}
                              aria-expanded={!!detailOpen}
                            >
                              {detailOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            </button>
                          ) : null}
                          <span className="inline-flex h-8 min-w-[2rem] items-center justify-center rounded-lg bg-slate-900 text-white text-xs font-bold tabular-nums">
                            #{row.rank || idx + 1}
                          </span>
                          {isBest && (
                            <Badge variant="success" className="font-bold gap-1 shadow-sm">
                              <Trophy className="h-3 w-3" /> Best quote
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4 align-top font-medium text-slate-900">
                        <span className="block">{(row.company_name || '').trim() || row.seller_name || '—'}</span>
                        {row.verified_supplier && (
                          <Badge variant="success" className="mt-2 text-[10px]">
                            Verified
                          </Badge>
                        )}
                      </td>
                      <td className="py-4 px-4 align-top font-semibold tabular-nums text-slate-900">{fmtInr(row.quoted_price ?? row.total_amount)}</td>
                      <td className="py-4 px-4 align-top text-slate-600">{row.delivery_days ?? '—'} days</td>
                      <td className="py-4 px-4 align-top tabular-nums text-slate-600">{row.available_qty ?? '—'}</td>
                      <td className="py-4 px-4 align-top">
                        {row.trust_score != null ? (
                          <Badge variant="primary" className="font-bold tabular-nums">
                            {Math.round(Number(row.trust_score))}%
                          </Badge>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-4 px-4 align-top">
                        {row.quote_score != null ? (
                          <Badge variant="teal" className="font-bold tabular-nums">
                            {row.quote_score}
                          </Badge>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-4 px-4 align-top text-xs text-slate-600">
                        {row.quote_valid_until ? formatDateIst(row.quote_valid_until) : '—'}
                        {expired && (
                          <Badge variant="danger" className="mt-2 block w-fit text-[10px] font-semibold">
                            Quote expired
                          </Badge>
                        )}
                      </td>
                      <td className="py-4 px-4 align-top">
                        <Badge variant={accepted ? 'success' : rejected ? 'danger' : 'default'} className="font-semibold capitalize">
                          {accepted ? 'Accepted' : rejected ? 'Rejected' : 'Pending'}
                        </Badge>
                      </td>
                      <td className="py-4 px-4 align-top whitespace-nowrap">
                        {accepted ? (
                          <div className="flex flex-col gap-2 items-start">
                            <Badge variant="success" className="font-semibold">
                              Accepted
                            </Badge>
                            {rfq.linkedOrderId ? (
                              <div className="flex flex-wrap gap-2">
                                <Link to={`/orders/${rfq.linkedOrderId}`}>
                                  <Button type="button" size="sm" variant="secondary" className="rounded-lg gap-1">
                                    <ExternalLink className="h-4 w-4" /> Open order
                                  </Button>
                                </Link>
                                <Link to={`/orders/${rfq.linkedOrderId}`} target="_blank" rel="noreferrer">
                                  <Button type="button" size="sm" className="rounded-lg gap-1">
                                    <Printer className="h-4 w-4" /> Print / PO
                                  </Button>
                                </Link>
                              </div>
                            ) : (
                              <Link to="/orders">
                                <Button type="button" size="sm" variant="secondary" className="rounded-lg">
                                  View orders
                                </Button>
                              </Link>
                            )}
                          </div>
                        ) : !rejected && rfq.status !== 'accepted' && quoteId && !expired ? (
                          <div className="flex flex-wrap gap-2">
                            <Button size="sm" className="rounded-lg shadow-sm" onClick={() => handleAcceptQuote(quoteId)} disabled={!!accepting}>
                              <CheckCircle className="h-4 w-4 mr-1" /> Accept
                            </Button>
                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              className="rounded-lg border-dashed"
                              onClick={() => {
                                setCounterOpen(quoteId);
                                setCounterText('');
                                setCounterTotal('');
                              }}
                              disabled={!!accepting}
                            >
                              <ArrowLeftRight className="h-4 w-4 mr-1" /> Counter
                            </Button>
                            <Button type="button" variant="secondary" size="sm" className="rounded-lg" onClick={() => handleRejectQuote(quoteId)} disabled={!!accepting}>
                              <XCircle className="h-4 w-4 mr-1" /> Reject
                            </Button>
                          </div>
                        ) : expired ? (
                          <span className="text-xs text-slate-400">—</span>
                        ) : null}
                      </td>
                    </tr>
                    {detailOpen && quoteMeta ? (
                      <tr className="bg-slate-50/95 border-b border-slate-200">
                        <td colSpan={10} className="p-0 align-top">
                          <div className="px-4 sm:px-6 py-5 sm:py-6 space-y-5 text-left">
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-sm font-bold text-slate-900">Full offer detail</p>
                              {quoteStatus === 'revised' ? (
                                <Badge variant="teal" className="text-[10px] font-bold">
                                  Revised
                                </Badge>
                              ) : null}
                            </div>
                            {(quoteMeta.createdAt || quoteMeta.created_at) && (
                              <p className="text-xs text-slate-500">
                                Submitted {formatDateTimeIst(quoteMeta.createdAt || quoteMeta.created_at, { dateStyle: 'medium', timeStyle: 'short' })}
                              </p>
                            )}
                            {(quoteMeta.updatedAt || quoteMeta.updated_at) && (
                              <p className="text-xs text-slate-500 -mt-2">
                                Last revised {formatDateTimeIst(quoteMeta.updatedAt || quoteMeta.updated_at, { dateStyle: 'medium', timeStyle: 'short' })}
                              </p>
                            )}
                            <div className="overflow-x-auto rounded-xl border border-slate-200/90 bg-white shadow-sm">
                              <table className="min-w-full text-sm">
                                <thead>
                                  <tr className="bg-slate-100/90 text-left text-xs uppercase tracking-wider text-slate-600">
                                    <th className="py-2.5 px-3 font-semibold">Product / line</th>
                                    <th className="py-2.5 px-3 font-semibold whitespace-nowrap">RFQ qty</th>
                                    <th className="py-2.5 px-3 font-semibold whitespace-nowrap">Unit price</th>
                                    <th className="py-2.5 px-3 font-semibold whitespace-nowrap">Offered qty</th>
                                    <th className="py-2.5 px-3 font-semibold whitespace-nowrap">Line total</th>
                                    <th className="py-2.5 px-3 font-semibold whitespace-nowrap">Delivery</th>
                                    <th className="py-2.5 px-3 font-semibold min-w-[8rem]">Line note</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {lineItems.length ? (
                                    lineItems.map((it, li) => {
                                      const pid = entityIdStr(it?.productId?._id || it?.productId);
                                      const wanted = rfqLineQty.get(pid);
                                      const off = it.availableQty;
                                      const sub = (it.unitPrice || 0) * (off || 0);
                                      return (
                                        <tr
                                          key={it.productId?._id?.toString?.() || it.productId?.id || li}
                                          className="border-t border-slate-100"
                                        >
                                          <td className="py-3 px-3 text-slate-900 font-medium">{lineItemLabel(it)}</td>
                                          <td className="py-3 px-3 text-slate-600 tabular-nums">{wanted != null ? wanted : '—'}</td>
                                          <td className="py-3 px-3 font-semibold tabular-nums text-slate-900">
                                            {fmtInr(it.unitPrice)}
                                          </td>
                                          <td className="py-3 px-3 text-slate-800 tabular-nums">{off ?? '—'}</td>
                                          <td className="py-3 px-3 font-semibold tabular-nums text-slate-900">
                                            {fmtInr(sub)}
                                          </td>
                                          <td className="py-3 px-3 text-slate-600 tabular-nums">
                                            {it.deliveryDays != null ? `${it.deliveryDays} days` : '—'}
                                          </td>
                                          <td className="py-3 px-3 text-slate-600 text-xs whitespace-pre-wrap break-words max-w-md">
                                            {it.itemNote?.trim() ? it.itemNote : '—'}
                                          </td>
                                        </tr>
                                      );
                                    })
                                  ) : (
                                    <tr>
                                      <td
                                        colSpan={7}
                                        className="py-6 px-3 text-sm text-amber-800 text-center bg-amber-50/50"
                                      >
                                        No line items were returned for this offer. Try refreshing; if this persists, contact
                                        support.
                                      </td>
                                    </tr>
                                  )}
                                </tbody>
                                {lineItems.length > 0 ? (
                                  <tfoot>
                                    <tr className="bg-teal-50/80 border-t-2 border-teal-200/60">
                                      <td colSpan={4} className="py-3 px-3 text-right text-sm font-bold text-slate-800">
                                        Quoted total (this offer)
                                      </td>
                                      <td className="py-3 px-3 text-sm font-bold text-teal-800 tabular-nums">
                                        {fmtInr(
                                          lineItems.reduce(
                                            (s, it) => s + (it.unitPrice || 0) * (it.availableQty || 0),
                                            0,
                                          ),
                                        )}
                                      </td>
                                      <td colSpan={2} className="py-3 px-3 text-xs text-slate-500">
                                        Excludes any taxes; refer to terms below if the seller provided GST or other charges.
                                      </td>
                                    </tr>
                                  </tfoot>
                                ) : null}
                              </table>
                            </div>
                            {quoteMeta.message ? (
                              <div className="rounded-xl border border-slate-200/90 bg-white p-4">
                                <p className="text-xs font-bold uppercase text-slate-500 mb-1.5">Seller message</p>
                                <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">{quoteMeta.message}</p>
                              </div>
                            ) : null}
                            {quoteMeta.commitmentNote || quoteMeta.deliveryCommitment ? (
                              <div className="rounded-xl border border-slate-200/90 bg-white p-4">
                                <p className="text-xs font-bold uppercase text-slate-500 mb-1.5">Delivery commitment</p>
                                <p className="text-sm text-slate-800 whitespace-pre-wrap">
                                  {quoteMeta.deliveryCommitment || quoteMeta.commitmentNote || '—'}
                                </p>
                                {quoteMeta.commitmentNote && quoteMeta.deliveryCommitment && quoteMeta.commitmentNote !== quoteMeta.deliveryCommitment && (
                                  <p className="text-sm text-slate-600 mt-2 whitespace-pre-wrap">{quoteMeta.commitmentNote}</p>
                                )}
                              </div>
                            ) : null}
                            {quoteMeta.warrantyOrSupportNote ? (
                              <div className="rounded-xl border border-slate-200/90 bg-white p-4">
                                <p className="text-xs font-bold uppercase text-slate-500 mb-1.5">Warranty & support</p>
                                <p className="text-sm text-slate-800 whitespace-pre-wrap">{quoteMeta.warrantyOrSupportNote}</p>
                              </div>
                            ) : null}
                            {quoteMeta.termsAndConditions ? (
                              <div className="rounded-xl border border-slate-200/90 bg-slate-900/5 p-4">
                                <p className="text-xs font-bold uppercase text-slate-500 mb-1.5">Terms & conditions</p>
                                <div className="text-sm text-slate-800 whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed pr-1">
                                  {quoteMeta.termsAndConditions}
                                </div>
                              </div>
                            ) : null}
                            {(() => {
                              const forQuote = counterOffers.filter((c) => String(c.quoteId || c.quote?._id || '') === quoteId);
                              if (!forQuote.length) return null;
                              return (
                                <div className="rounded-xl border border-amber-200/90 bg-amber-50/40 p-4">
                                  <p className="text-xs font-bold uppercase text-amber-900/90 mb-2">Buyer counter-offers on this quote</p>
                                  <ul className="space-y-2">
                                    {forQuote.map((c) => (
                                      <li key={c._id || c.id} className="text-sm text-amber-950/90">
                                        <span className="text-xs text-amber-800/80">
                                          {c.createdAt
                                            ? formatDateTimeIst(c.createdAt, { dateStyle: 'short', timeStyle: 'short' })
                                            : ''}
                                        </span>
                                        {c.proposedTotal != null && c.proposedTotal !== '' && (
                                          <span className="ml-2 font-semibold">Target ≈ ₹{Number(c.proposedTotal).toLocaleString('en-IN')}</span>
                                        )}
                                        <p className="whitespace-pre-wrap mt-0.5">{c.message}</p>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              );
                            })()}
                          </div>
                        </td>
                      </tr>
                    ) : null}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {counterOffers.length > 0 && (
        <Card className="border-slate-200/90">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="section-title">Counter-offers</h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Buyer terms in response to supplier quotes. Suppliers reply with <span className="font-semibold text-slate-700">Revise quote</span> on
              the RFQ.
            </p>
          </div>
          <ul className="divide-y divide-slate-100">
            {counterOffers.map((c) => (
              <li key={c._id || c.id} className="px-5 py-4 text-sm">
                <p className="text-xs text-slate-400 tabular-nums">
                  {c.createdAt ? formatDateTimeIst(c.createdAt, { dateStyle: 'medium', timeStyle: 'short' }) : ''}
                </p>
                <p className="text-slate-500 mt-1">
                  <span className="font-mono text-xs">Quote #{String(c.quoteId || '').slice(-6)}</span>
                  {c.proposedTotal != null && c.proposedTotal !== '' && (
                    <span className="ml-2 font-semibold text-slate-800">Target ≈ ₹{Number(c.proposedTotal).toLocaleString('en-IN')}</span>
                  )}
                </p>
                <p className="mt-2 text-slate-800 whitespace-pre-wrap leading-relaxed">{c.message}</p>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <div className="grid lg:grid-cols-1 gap-8">
        <Card className="border-slate-200/90 lg:col-span-1">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="section-title flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-teal-600" /> Messages
              </h2>
              <p className="text-sm text-slate-500 mt-1">Keep negotiation on-platform for audit and safety.</p>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed max-w-2xl">
                To protect buyers and sellers, sharing phone numbers, emails, or external contact details is restricted.
              </p>
            </div>
          </div>
          <div className="p-5 sm:p-6">
            <div className="space-y-3 max-h-80 overflow-y-auto mb-5 pr-1 rounded-xl border border-slate-100 bg-slate-50/30 p-3">
              {thread?.messages?.length ? (
                thread.messages.map((m) => {
                  const mine = (m.senderId?._id?.toString() || m.senderId?.toString()) === uid;
                  return (
                    <div
                      key={m._id || m.id}
                      className={`flex ${mine ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[min(100%,28rem)] rounded-2xl px-4 py-3 shadow-sm ${
                          mine
                            ? 'bg-teal-600 text-white rounded-br-md'
                            : 'bg-white border border-slate-200 text-slate-800 rounded-bl-md'
                        }`}
                      >
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <span className={`text-xs font-semibold ${mine ? 'text-teal-100' : 'text-slate-500'}`}>{m.senderId?.name}</span>
                          {m.senderRole && (
                            <Badge variant={mine ? 'outline' : 'default'} className={`!text-[10px] ${mine ? '!ring-white/30 !text-white' : ''}`}>
                              {m.senderRole}
                            </Badge>
                          )}
                          {m.moderationFlag && (
                            <Badge variant="warning" className="text-[10px]">
                              Flagged for review
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm leading-relaxed">{m.displayMessage ?? m.text}</p>
                        {m.moderationReason && (
                          <p className={`text-xs mt-2 ${mine ? 'text-amber-200' : 'text-amber-800'}`}>Note: {m.moderationReason}</p>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-slate-500 text-sm text-center py-8">No messages yet — start the thread below.</p>
              )}
            </div>
            <form onSubmit={handleSendMessage} className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 min-w-0">
                <Input
                  value={messageText}
                  onChange={(e) => {
                    setMessageText(e.target.value);
                    setComposerBlockedHighlight(false);
                  }}
                  placeholder="Write a message to participants…"
                  className={composerBlockedHighlight ? '!border-red-500 !ring-2 !ring-red-400' : ''}
                />
              </div>
              <Button type="submit" size="md" className="gap-2 shrink-0 rounded-xl sm:w-auto w-full">
                <Send className="h-4 w-4" /> Send
              </Button>
            </form>
          </div>
        </Card>
      </div>

      {counterOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="counter-offer-title"
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl ring-1 ring-slate-200" onClick={(e) => e.stopPropagation()}>
            <h3 id="counter-offer-title" className="text-lg font-semibold text-slate-900">
              Send counter-offer
            </h3>
            <p className="mt-2 text-sm text-slate-600">
              The supplier is notified to revise their quote. Be specific on price, delivery, or other terms.
            </p>
            <form
              onSubmit={handlePostCounter}
              className="mt-4 space-y-3"
              onClick={(e) => e.stopPropagation()}
            >
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Message</label>
                <textarea
                  value={counterText}
                  onChange={(e) => setCounterText(e.target.value)}
                  rows={4}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  placeholder="E.g. Need unit price at ₹1.50 for line 1 and 12-day delivery on both lines."
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Target total (optional, INR)</label>
                <Input
                  value={counterTotal}
                  onChange={(e) => setCounterTotal(e.target.value)}
                  type="text"
                  inputMode="decimal"
                  placeholder="e.g. 580"
                  className="mt-1"
                />
              </div>
              <div className="flex flex-col-reverse sm:flex-row gap-2 sm:justify-end pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  className="rounded-xl"
                  onClick={() => {
                    setCounterOpen(null);
                    setCounterText('');
                    setCounterTotal('');
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="rounded-xl" disabled={postingCounter}>
                  {postingCounter ? 'Sending…' : 'Send counter-offer'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {moderationConfirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="moderation-confirm-title"
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
            <h3 id="moderation-confirm-title" className="text-lg font-semibold text-slate-900">
              Possible contact details detected
            </h3>
            <p className="mt-3 text-sm text-slate-600 leading-relaxed">
              B2Bभारत detected content that may contain a phone number, email, or request to move outside the platform.
              Please edit the message or confirm sending for admin review.
            </p>
            <div className="mt-6 flex flex-col-reverse sm:flex-row gap-2 sm:justify-end">
              <Button
                type="button"
                variant="secondary"
                className="rounded-xl"
                onClick={() => setModerationConfirmOpen(false)}
              >
                Edit message
              </Button>
              <Button type="button" className="rounded-xl" onClick={() => void handleConfirmModerationSend()}>
                Send for review
              </Button>
            </div>
          </div>
        </div>
      )}

    </motion.div>
  );
}
