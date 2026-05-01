from pathlib import Path

p = Path(__file__).resolve().parent.parent / "src" / "pages" / "OrderDetail.jsx"
t = p.read_text("utf-8")
t = t.replace(
    "import { Package, Clock, Shield, Check, Truck, Box, Sparkles, Printer } from 'lucide-react';",
    "import { Package, Clock, Check, Truck, Box, Sparkles, Printer } from 'lucide-react';",
    1,
)
t = t.replace(
    "  const [paymentUpdating, setPaymentUpdating] = useState(false);\n  const toast = useToast();",
    "  const toast = useToast();",
    1,
)
hp = """  const handlePayment = async (paymentStatus) => {
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
t = t.replace(hp, "", 1)
p.write_text(t, "utf-8")
print("ok")
