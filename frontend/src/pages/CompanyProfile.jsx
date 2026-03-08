import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { companyApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';

export default function CompanyProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    companyName: '',
    description: '',
    city: '',
    state: '',
    country: 'India',
    phone: '',
    website: '',
    gstNumber: '',
  });
  const toast = useToast();

  useEffect(() => {
    companyApi
      .getMe()
      .then((res) => {
        const c = res.data.data.company;
        setProfile(c);
        setForm({
          companyName: c.companyName || '',
          description: c.description || '',
          city: c.city || '',
          state: c.state || '',
          country: c.country || 'India',
          phone: c.phone || '',
          website: c.website || '',
          gstNumber: c.gstNumber || '',
        });
      })
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const { data } = await companyApi.upsert(form);
      setProfile(data.data.company);
      toast.add('Company profile saved.', 'success');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save.');
    }
  };

  if (loading) {
    return (
      <div className="max-w-xl space-y-4 animate-pulse">
        <div className="h-8 w-48 bg-neutral-200 rounded" />
        <div className="h-12 bg-neutral-200 rounded" />
        <div className="h-12 bg-neutral-200 rounded" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="max-w-xl">
      <h1 className="text-2xl font-bold text-neutral-900 mb-2">Company Profile</h1>
      <p className="text-neutral-500 mb-6">Your business details shown to buyers.</p>
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg">{error}</div>
      )}
      <Card>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <Input
            label="Company name *"
            value={form.companyName}
            onChange={(e) => setForm((f) => ({ ...f, companyName: e.target.value }))}
            required
          />
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={3}
              className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="City" value={form.city} onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))} />
            <Input label="State" value={form.state} onChange={(e) => setForm((f) => ({ ...f, state: e.target.value }))} />
          </div>
          <Input label="Country" value={form.country} onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))} />
          <Input label="Phone" value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
          <Input label="Website" type="url" value={form.website} onChange={(e) => setForm((f) => ({ ...f, website: e.target.value }))} />
          <Input label="GST number" value={form.gstNumber} onChange={(e) => setForm((f) => ({ ...f, gstNumber: e.target.value }))} />
          <Button type="submit">Save profile</Button>
        </form>
      </Card>
    </motion.div>
  );
}
