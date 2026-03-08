import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Send, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { rfqApi, messagesApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export default function RFQDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [rfq, setRfq] = useState(null);
  const [quotes, setQuotes] = useState([]);
  const [thread, setThread] = useState(null);
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(null);
  const toast = useToast();

  useEffect(() => {
    rfqApi.getById(id)
      .then((res) => setRfq(res.data.data.rfq))
      .catch(() => setRfq(null))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!rfq) return;
    rfqApi.getQuotes(id).then((res) => setQuotes(res.data.data.quotes || [])).catch(() => setQuotes([]));
    messagesApi.get(id).then((res) => setThread(res.data.data.thread)).catch(() => setThread(null));
  }, [rfq, id]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!messageText.trim()) return;
    try {
      const { data } = await messagesApi.post(id, messageText);
      setThread(data.data.thread);
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
      rfqApi.getById(id).then((res) => setRfq(res.data.data.rfq));
      setQuotes((prev) => prev.map((q) => (q._id === quoteId ? { ...q, status: 'accepted' } : { ...q, status: 'rejected' })));
    } catch (e) {
      toast.add(e.response?.data?.message || 'Failed to accept quote', 'error');
    } finally {
      setAccepting(null);
    }
  };

  if (loading || !rfq) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;

  const buyerIdStr = rfq.buyerId?._id?.toString() || rfq.buyerId?.toString();
  const isBuyer = user && (user.id?.toString() || user._id?.toString()) === buyerIdStr;

  const steps = [
    { key: 'sent', label: 'Created' },
    { key: 'quoted', label: 'Quoted' },
    { key: 'accepted', label: 'Accepted' },
    { key: 'accepted', label: 'Order Generated' },
  ];
  const stepIndex = rfq.status === 'accepted' ? 3 : rfq.status === 'quoted' ? 2 : 1;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold">RFQ #{rfq._id.slice(-6)}</h1>
        <Badge variant={rfq.status === 'accepted' ? 'success' : rfq.status === 'closed' || rfq.status === 'rejected' ? 'danger' : 'warning'}>{rfq.status}</Badge>
      </div>

      {/* Stepper */}
      <Card>
        <div className="p-4">
          <div className="flex items-center justify-between text-sm">
            {steps.map((step, i) => (
              <div key={i} className="flex flex-1 items-center">
                <div className={`flex flex-col items-center ${i <= stepIndex ? 'text-primary-600' : 'text-neutral-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${i <= stepIndex ? 'bg-primary-100 text-primary-700' : 'bg-neutral-100'}`}>
                    {i + 1}
                  </div>
                  <span className="mt-1">{step.label}</span>
                </div>
                {i < steps.length - 1 && <div className={`flex-1 h-0.5 mx-1 ${i < stepIndex ? 'bg-primary-200' : 'bg-neutral-200'}`} />}
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <h2 className="font-medium mb-2">Items</h2>
          <ul className="space-y-2">
            {rfq.items?.map((item, i) => (
              <li key={i} className="flex justify-between text-sm">
                <span>{item.productId?.title || item.productId}</span>
                <span>Qty: {item.quantity}</span>
              </li>
            ))}
          </ul>
        </div>
      </Card>

      {isBuyer && quotes.length > 0 && (
        <Card>
          <div className="p-4">
            <h2 className="font-medium mb-4">Quote comparison</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Seller</th>
                    <th className="text-left py-2">Quoted price</th>
                    <th className="text-left py-2">Delivery (days)</th>
                    <th className="text-left py-2">Trust score</th>
                    <th className="text-left py-2">Quote score</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-left py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {[...quotes].sort((a, b) => (b.quoteScore ?? 0) - (a.quoteScore ?? 0)).map((q) => {
                    const total = q.items?.reduce((s, i) => s + (i.unitPrice || 0) * (i.availableQty || 0), 0) || 0;
                    return (
                      <tr key={q._id} className="border-b">
                        <td className="py-2">
                          <span>{q.sellerId?.name}</span>
                          {q.sellerId?.isVerifiedSupplier && <Badge variant="success" className="ml-1 text-xs">Verified</Badge>}
                        </td>
                        <td className="py-2">₹{total}</td>
                        <td className="py-2">{q.items?.[0]?.deliveryDays ?? '—'}</td>
                        <td className="py-2">{q.sellerId?.trustScore != null ? `${q.sellerId.trustScore}%` : '—'}</td>
                        <td className="py-2 font-medium">{q.quoteScore != null ? q.quoteScore : '—'}</td>
                        <td className="py-2"><Badge variant={q.status === 'accepted' ? 'success' : q.status === 'rejected' ? 'danger' : 'default'}>{q.status}</Badge></td>
                        <td className="py-2">
                          {q.status === 'accepted' ? (
                            <Badge variant="success">Accepted</Badge>
                          ) : q.status !== 'rejected' && rfq.status !== 'accepted' ? (
                            <Button size="sm" onClick={() => handleAcceptQuote(q._id)} disabled={!!accepting}>
                              <CheckCircle className="h-4 w-4 mr-1" /> Accept quote
                            </Button>
                          ) : null}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      )}

      <Card>
        <div className="p-4">
          <h2 className="font-medium mb-4">Messages</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
            {thread?.messages?.length ? (
              thread.messages.map((m) => (
                <div key={m._id} className={`p-2 rounded ${(m.senderId?._id?.toString() || m.senderId?.toString()) === (user?.id?.toString() || user?._id?.toString()) ? 'bg-primary-50 ml-4' : 'bg-neutral-100 mr-4'}`}>
                  <span className="text-xs text-neutral-500">{m.senderId?.name}</span>
                  <p className="text-sm">{m.text}</p>
                </div>
              ))
            ) : (
              <p className="text-neutral-500 text-sm">No messages yet.</p>
            )}
          </div>
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 border rounded-lg px-3 py-2"
            />
            <Button type="submit" size="sm" className="gap-1"><Send className="h-4 w-4" /> Send</Button>
          </form>
        </div>
      </Card>
    </motion.div>
  );
}
