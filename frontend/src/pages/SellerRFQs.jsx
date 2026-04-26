import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, Send, Pencil } from 'lucide-react';
import { rfqApi, quoteApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { Input } from '../components/ui/Input';

function productIdStr(item) {
  const p = item?.productId;
  if (!p) return '';
  if (typeof p === 'string') return p;
  return p._id || p.id || '';
}

function sellerIdFromProduct(item) {
  const p = item?.productId;
  if (!p || typeof p !== 'object') return null;
  const s = p.seller;
  if (s && typeof s === 'object') return String(s._id || s.id || '');
  if (s) return String(s);
  return null;
}

function defaultValidUntilISO() {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + 14);
  d.setUTCHours(23, 59, 0, 0);
  return d.toISOString();
}

function toDatetimeLocalValue(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function SellerRFQs() {
  const { user } = useAuth();
  const [rfqs, setRfqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalRfq, setModalRfq] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [existingQuote, setExistingQuote] = useState(null);
  const [myItems, setMyItems] = useState([]);
  const [lines, setLines] = useState({});
  const [quoteValidUntil, setQuoteValidUntil] = useState('');
  const [sellerMessage, setSellerMessage] = useState('');
  const [terms, setTerms] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const toast = useToast();

  const loadRfqs = useCallback(() => {
    rfqApi
      .getAssigned()
      .then((res) => setRfqs(res.data.data.rfqs || []))
      .catch(() => setRfqs([]));
  }, []);

  useEffect(() => {
    setLoading(true);
    rfqApi
      .getAssigned()
      .then((res) => setRfqs(res.data.data.rfqs || []))
      .catch(() => setRfqs([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!modalRfq || !user) return;
    const uid = user.id?.toString() || user._id?.toString();
    let cancelled = false;
    setModalLoading(true);
    setFieldErrors({});

    (async () => {
      try {
        const quotesRes = await rfqApi.getQuotes(modalRfq._id);
        const quotes = quotesRes.data.data.quotes || [];
        const mine = quotes.find((q) => String(q.sellerId?._id || q.sellerId?.id || q.sellerId) === uid) || null;

        const items = modalRfq.items || [];
        const filtered = items.filter((it) => sellerIdFromProduct(it) === uid);

        const nextLines = {};
        for (const it of filtered) {
          const pid = productIdStr(it);
          const prod = typeof it.productId === 'object' ? it.productId : null;
          const basePrice = prod?.price != null ? Number(prod.price) : 0;
          const qty = Number(it.quantity) > 0 ? Number(it.quantity) : 1;
          if (mine?.items?.length) {
            const li = mine.items.find((x) => String(productIdStr({ productId: x.productId })) === pid);
            nextLines[pid] = {
              unitPrice: (li?.unitPrice ?? basePrice) || '',
              availableQty: li?.availableQty ?? qty,
              deliveryDays: li?.deliveryDays ?? 7,
              itemNote: li?.itemNote || '',
            };
          } else {
            nextLines[pid] = {
              unitPrice: basePrice > 0 ? basePrice : '',
              availableQty: qty,
              deliveryDays: 7,
              itemNote: '',
            };
          }
        }

        if (cancelled) return;
        setMyItems(filtered);
        setExistingQuote(mine);
        setLines(nextLines);
        setSellerMessage(mine?.message || '');
        setTerms(mine?.termsAndConditions || '');
        const vUntil = mine?.quoteValidUntil || defaultValidUntilISO();
        setQuoteValidUntil(toDatetimeLocalValue(vUntil));
      } catch {
        if (!cancelled) toast.add('Could not load quote context', 'error');
      } finally {
        if (!cancelled) setModalLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [modalRfq, user, toast]);

  const validate = () => {
    const err = {};
    const until = new Date(quoteValidUntil);
    if (!quoteValidUntil || Number.isNaN(until.getTime())) {
      err.quoteValidUntil = 'Choose a valid date and time.';
    } else if (until.getTime() <= Date.now()) {
      err.quoteValidUntil = 'Quote must be valid until a future date/time.';
    }
    for (const it of myItems) {
      const pid = productIdStr(it);
      const row = lines[pid] || {};
      const up = Number(row.unitPrice);
      const aq = Number(row.availableQty);
      const dd = Number(row.deliveryDays);
      if (!(up > 0)) err[`price_${pid}`] = 'Unit price must be greater than 0.';
      if (!(aq > 0)) err[`qty_${pid}`] = 'Available quantity must be greater than 0.';
      if (!(dd > 0)) err[`del_${pid}`] = 'Delivery days must be greater than 0.';
    }
    setFieldErrors(err);
    return Object.keys(err).length === 0;
  };

  const buildPayload = () => {
    const items = myItems.map((it) => {
      const pid = productIdStr(it);
      const row = lines[pid];
      return {
        productId: pid,
        unitPrice: Number(row.unitPrice),
        availableQty: Number(row.availableQty),
        deliveryDays: Number(row.deliveryDays),
        itemNote: (row.itemNote || '').trim() || undefined,
      };
    });
    const isoUntil = new Date(quoteValidUntil).toISOString();
    return {
      items,
      message: sellerMessage.trim() || undefined,
      termsAndConditions: terms.trim() || undefined,
      quoteValidUntil: isoUntil,
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!modalRfq || !validate()) {
      toast.add('Please fix the highlighted fields.', 'error');
      return;
    }
    setSubmitting(true);
    const payload = buildPayload();
    try {
      if (existingQuote?._id) {
        await quoteApi.update(existingQuote._id, {
          items: payload.items,
          message: sellerMessage,
          termsAndConditions: terms,
          quoteValidUntil: payload.quoteValidUntil,
        });
        toast.add('Quote revised successfully.', 'success');
      } else {
        await rfqApi.submitQuote(modalRfq._id, payload);
        toast.add('Quote submitted successfully.', 'success');
      }
      window.dispatchEvent(new CustomEvent('smartb2b:rfq-updated', { detail: { rfqId: modalRfq._id } }));
      setModalRfq(null);
      setExistingQuote(null);
      loadRfqs();
    } catch (err) {
      const d = err.response?.data?.detail;
      const msg =
        (typeof d === 'object' && d && d.message) ||
        err.response?.data?.message ||
        (typeof d === 'string' ? d : null) ||
        'Failed to save quote';
      toast.add(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const updateLine = (pid, key, value) => {
    setLines((prev) => ({
      ...prev,
      [pid]: { ...prev[pid], [key]: value },
    }));
  };

  if (loading) return <div className="animate-pulse h-64 bg-slate-100 rounded-xl" />;
  if (!rfqs.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6 text-slate-900">RFQs for you</h1>
        <Card>
          <EmptyState icon={FileText} title="No RFQs assigned" description="RFQs containing your products will appear here." />
        </Card>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6 text-slate-900">RFQs for you</h1>
      <div className="space-y-4">
        {rfqs.map((rfq) => (
          <Card key={rfq._id} className="border-slate-200/90">
            <div className="p-4 flex flex-wrap items-center justify-between gap-2">
              <div>
                <Link to={`/rfq/${rfq._id}`} className="font-medium text-teal-700 hover:text-teal-800 hover:underline">
                  RFQ #{String(rfq._id).slice(-6)}
                </Link>
                <span className="text-slate-500 text-sm ml-2">Buyer: {rfq.buyerId?.name}</span>
                <span className="ml-2 text-slate-500 text-sm">{rfq.items?.length || 0} item(s)</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="primary" className="capitalize">
                  {rfq.status}
                </Badge>
                <Button size="sm" className="rounded-xl gap-1" onClick={() => setModalRfq(rfq)}>
                  {rfq.status === 'quoted' ? <Pencil className="h-4 w-4" /> : <Send className="h-4 w-4" />}
                  {rfq.status === 'quoted' ? 'Quote / Revise' : 'Submit quote'}
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {modalRfq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => !submitting && setModalRfq(null)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl p-5 sm:p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-xl border border-slate-200"
            onClick={(ev) => ev.stopPropagation()}
          >
            <h3 className="font-bold text-lg text-slate-900 mb-1">
              {existingQuote ? 'Revise quote' : 'Submit quote'} — RFQ #{String(modalRfq._id).slice(-6)}
            </h3>
            <p className="text-sm text-slate-500 mb-4">
              Enter pricing for each of your catalog lines on this RFQ. Buyers compare on price, delivery, and trust score.
            </p>

            {modalLoading ? (
              <div className="h-40 bg-slate-100 rounded-xl animate-pulse" />
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {myItems.map((it) => {
                  const pid = productIdStr(it);
                  const title = typeof it.productId === 'object' ? it.productId?.title : 'Product';
                  const row = lines[pid] || {};
                  return (
                    <div key={pid} className="rounded-xl border border-slate-200 p-4 space-y-3 bg-slate-50/50">
                      <p className="font-semibold text-slate-900 text-sm">{title}</p>
                      <p className="text-xs text-slate-500">RFQ requested qty: {it.quantity}</p>
                      <div className="grid grid-cols-2 gap-3">
                        <Input
                          label="Unit price (₹)"
                          type="number"
                          step="0.01"
                          min="0"
                          value={row.unitPrice}
                          onChange={(e) => updateLine(pid, 'unitPrice', e.target.value)}
                          error={fieldErrors[`price_${pid}`]}
                        />
                        <Input
                          label="Available qty"
                          type="number"
                          min="1"
                          value={row.availableQty}
                          onChange={(e) => updateLine(pid, 'availableQty', e.target.value)}
                          error={fieldErrors[`qty_${pid}`]}
                        />
                        <Input
                          label="Delivery (days)"
                          type="number"
                          min="1"
                          value={row.deliveryDays}
                          onChange={(e) => updateLine(pid, 'deliveryDays', e.target.value)}
                          error={fieldErrors[`del_${pid}`]}
                          className="col-span-2"
                        />
                      </div>
                      <Input
                        label="Line note (optional)"
                        value={row.itemNote}
                        onChange={(e) => updateLine(pid, 'itemNote', e.target.value)}
                        placeholder="Lead time, incoterms, packaging…"
                      />
                    </div>
                  );
                })}

                <Input
                  label="Quote valid until"
                  type="datetime-local"
                  value={quoteValidUntil}
                  onChange={(e) => setQuoteValidUntil(e.target.value)}
                  error={fieldErrors.quoteValidUntil}
                />

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Message to buyer</label>
                  <textarea
                    value={sellerMessage}
                    onChange={(e) => setSellerMessage(e.target.value)}
                    rows={2}
                    className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                    placeholder="Covering letter, assumptions, or clarifications…"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Terms &amp; conditions</label>
                  <textarea
                    value={terms}
                    onChange={(e) => setTerms(e.target.value)}
                    rows={3}
                    className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                    placeholder="Warranty, payment terms, exclusions…"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <Button type="button" variant="secondary" className="rounded-xl" disabled={submitting} onClick={() => setModalRfq(null)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="rounded-xl" disabled={submitting || modalLoading}>
                    {submitting ? 'Saving…' : existingQuote ? 'Save revision' : 'Submit quote'}
                  </Button>
                </div>
              </form>
            )}
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
