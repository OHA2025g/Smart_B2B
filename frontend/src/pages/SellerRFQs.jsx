import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, Send } from 'lucide-react';
import { rfqApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';

export default function SellerRFQs() {
  const [rfqs, setRfqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalRfq, setModalRfq] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const toast = useToast();

  useEffect(() => {
    rfqApi.getAssigned()
      .then((res) => setRfqs(res.data.data.rfqs || []))
      .catch(() => setRfqs([]))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmitQuote = async (e) => {
    e.preventDefault();
    if (!modalRfq) return;
    setSubmitting(true);
    try {
      await rfqApi.submitQuote(modalRfq._id, {});
      toast.add('Quote submitted', 'success');
      setModalRfq(null);
      rfqApi.getAssigned().then((res) => setRfqs(res.data.data.rfqs || []));
    } catch (err) {
      toast.add(err.response?.data?.message || 'Failed to submit quote', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;
  if (!rfqs.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">RFQs for you</h1>
        <Card>
          <EmptyState icon={FileText} title="No RFQs assigned" description="RFQs containing your products will appear here." />
        </Card>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-2xl font-bold mb-6">RFQs for you</h1>
      <div className="space-y-4">
        {rfqs.map((rfq) => (
          <Card key={rfq._id}>
            <div className="p-4 flex flex-wrap items-center justify-between gap-2">
              <div>
                <Link to={`/rfq/${rfq._id}`} className="font-medium text-primary-600 hover:underline">RFQ #{rfq._id.slice(-6)}</Link>
                <span className="text-neutral-500 text-sm ml-2">Buyer: {rfq.buyerId?.name}</span>
                <span className="ml-2 text-neutral-500 text-sm">{rfq.items?.length || 0} item(s)</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="primary">{rfq.status}</Badge>
                <Button size="sm" onClick={() => setModalRfq(rfq)}>
                  <Send className="h-4 w-4 mr-1" /> Submit Quote
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {modalRfq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setModalRfq(null)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl p-6 max-w-md w-full shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-semibold mb-4">Submit quote for RFQ #{modalRfq._id.slice(-6)}</h3>
            <p className="text-sm text-neutral-500 mb-4">Default prices from your products will be used. You can revise the quote later.</p>
            <form onSubmit={handleSubmitQuote} className="flex gap-2">
              <Button type="button" variant="secondary" onClick={() => setModalRfq(null)}>Cancel</Button>
              <Button type="submit" disabled={submitting}>{submitting ? 'Submitting...' : 'Submit Quote'}</Button>
            </form>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
