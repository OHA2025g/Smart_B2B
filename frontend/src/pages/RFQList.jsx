import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';
import { rfqApi } from '../api/client';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';

const statusVariant = (s) => (s === 'accepted' ? 'success' : s === 'rejected' || s === 'closed' ? 'danger' : 'warning');

export default function RFQList() {
  const [rfqs, setRfqs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    rfqApi.getMy()
      .then((res) => setRfqs(res.data.data.rfqs || []))
      .catch(() => setRfqs([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />;
  if (!rfqs.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">My RFQs</h1>
        <Card>
          <EmptyState
            icon={FileText}
            title="No RFQs yet"
            description="Add products to your cart and create an RFQ to get quotes from sellers."
            action={<Link to="/cart"><button className="text-primary-600 font-medium">Go to cart</button></Link>}
          />
        </Card>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-2xl font-bold mb-6">My RFQs</h1>
      <div className="space-y-4">
        {rfqs.map((rfq) => (
          <Link key={rfq._id} to={`/rfq/${rfq._id}`}>
            <Card className="hover:shadow-md transition-shadow">
              <div className="p-4 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span className="font-medium text-neutral-900">RFQ </span>
                  <span className="text-neutral-500 text-sm">#{rfq._id.slice(-6)}</span>
                  <span className="ml-2 text-neutral-500 text-sm">{rfq.items?.length || 0} item(s)</span>
                </div>
                <Badge variant={statusVariant(rfq.status)}>{rfq.status}</Badge>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </motion.div>
  );
}
