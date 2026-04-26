import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Send, CheckCircle, Clock, MessageSquare, Trophy, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { rfqApi, messagesApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

export default function RFQDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [rfq, setRfq] = useState(null);
  const [quotes, setQuotes] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [thread, setThread] = useState(null);
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(null);
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
    const buyerIdStr = rfq.buyerId?._id?.toString() || rfq.buyerId?.toString();
    const isRfqBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;
    if (isRfqBuyer) {
      rfqApi.getQuoteComparison(id).then((res) => setComparison(res.data.data.comparison || [])).catch(() => setComparison([]));
    } else {
      setComparison([]);
    }
    rfqApi.getTimeline(id).then((res) => setTimeline(res.data.data.timeline || [])).catch(() => setTimeline([]));
    messagesApi.get(id).then((res) => setThread(res.data.data.thread)).catch(() => setThread(null));
  }, [rfq, id, user]);

  useEffect(() => {
    const onRfqUpdated = (e) => {
      if (!id || e.detail?.rfqId !== id) return;
      rfqApi
        .getById(id)
        .then((res) => {
          const next = res.data.data.rfq;
          setRfq(next);
          const buyerStr = next.buyerId?._id?.toString() || next.buyerId?.toString();
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
    };
    window.addEventListener('smartb2b:rfq-updated', onRfqUpdated);
    return () => window.removeEventListener('smartb2b:rfq-updated', onRfqUpdated);
  }, [id, user]);

  const recommended = useMemo(() => {
    if (!rfq) return null;
    if (comparison.length) {
      const row = comparison.find((r) => r.rank === 1) || comparison[0];
      return row
        ? {
            company: row.company_name || row.seller_name,
            price: row.quoted_price,
            delivery: row.delivery_days,
            trust: row.trust_score,
            score: row.quote_score,
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
      company: q.sellerId?.name,
      price: tp,
      delivery: Math.round(avgDel),
      trust: q.sellerId?.trustScore,
      score: q.quoteScore,
    };
  }, [rfq, comparison, quotes]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!messageText.trim()) return;
    try {
      const { data } = await messagesApi.post(id, messageText);
      setThread(data.data.thread);
      const msgs = data.data.thread?.messages || [];
      const last = msgs[msgs.length - 1];
      if (last?.moderationFlag || last?.containsContactAttempt) {
        toast.add('Please keep communication on the platform — your message was flagged for review.', 'error');
      } else {
        toast.add('Message sent', 'success');
      }
      setMessageText('');
    } catch {
      toast.add('Failed to send message', 'error');
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

  const buyerIdStr = rfq.buyerId?._id?.toString() || rfq.buyerId?.toString();
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
                      {e.created_at ? new Date(e.created_at).toLocaleString() : ''}
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
                    <span className="font-semibold text-slate-800">Why:</span> Best balance of price, delivery speed, and supplier
                    trust score.
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
                  const quoteId = row.quoteId || quotes[idx]?._id;
                  const quoteStatus = quotes.find((q) => q._id === quoteId)?.status ?? row.status;
                  const accepted = quoteStatus === 'accepted';
                  const rejected = quoteStatus === 'rejected';
                  const isBest = row.best_quote || (comparison.length > 0 && row.rank === 1);
                  const expired = row.is_expired || quotes.find((q) => q._id === quoteId)?.isQuoteExpired;
                  return (
                    <tr
                      key={row.quoteId || idx}
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
                        <span className="block">{row.seller_name}</span>
                        {row.verified_supplier && (
                          <Badge variant="success" className="mt-2 text-[10px]">
                            Verified
                          </Badge>
                        )}
                      </td>
                      <td className="py-4 px-4 align-top font-semibold tabular-nums text-slate-900">₹{row.quoted_price ?? row.total_amount ?? 0}</td>
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
                        {row.quote_valid_until ? new Date(row.quote_valid_until).toLocaleDateString() : '—'}
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
                          <Badge variant="success" className="font-semibold">
                            Accepted
                          </Badge>
                        ) : !rejected && rfq.status !== 'accepted' && quoteId && !expired ? (
                          <Button size="sm" className="rounded-lg shadow-sm" onClick={() => handleAcceptQuote(quoteId)} disabled={!!accepting}>
                            <CheckCircle className="h-4 w-4 mr-1" /> Accept
                          </Button>
                        ) : expired ? (
                          <span className="text-xs text-slate-400">—</span>
                        ) : null}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
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
                          {m.moderationFlag && <Badge variant="warning" className="text-[10px]">Review</Badge>}
                        </div>
                        <p className="text-sm leading-relaxed">{m.text}</p>
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
                  onChange={(e) => setMessageText(e.target.value)}
                  placeholder="Write a message to participants…"
                />
              </div>
              <Button type="submit" size="md" className="gap-2 shrink-0 rounded-xl sm:w-auto w-full">
                <Send className="h-4 w-4" /> Send
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
