import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bell, Check, CheckCheck } from 'lucide-react';
import { notificationsApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';

function getLink(notification) {
  const type = notification.related_entity_type;
  const id = notification.related_entity_id;
  if (!id) return null;
  if (type === 'rfq') return `/rfq/${id}`;
  if (type === 'order') return `/dashboard`;
  if (type === 'user') return `/suppliers/${id}`;
  return null;
}

export default function Notifications() {
  const [list, setList] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const load = () => {
    notificationsApi
      .getMe()
      .then((r) => {
        setList(r.data.data?.notifications || []);
        setUnreadCount(r.data.data?.unreadCount ?? 0);
      })
      .catch(() => setList([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(), []);

  const handleMarkRead = (n) => {
    if (n.is_read) return;
    notificationsApi.markRead(n.id || n._id).then(() => load()).catch(() => toast.add('Failed to mark as read', 'error'));
  };

  const handleMarkAllRead = () => {
    notificationsApi.markAllRead().then(() => {
      load();
      toast.add('All marked as read', 'success');
    }).catch(() => toast.add('Failed', 'error'));
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-neutral-200 rounded animate-pulse" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-neutral-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Bell className="h-7 w-7 text-teal-600" /> Notifications
        </h1>
        {list.length > 0 && list.some((n) => !n.is_read) && (
          <Button variant="secondary" size="sm" onClick={handleMarkAllRead} className="gap-1">
            <CheckCheck className="h-4 w-4" /> Mark all read
          </Button>
        )}
      </div>

      {list.length === 0 ? (
        <EmptyState
          title="No notifications"
          description="You're all caught up."
        />
      ) : (
        <div className="space-y-2">
          {list.map((n) => {
            const link = getLink(n);
            const content = (
              <Card className={n.is_read ? 'opacity-80' : ''}>
                <div className="p-4 flex items-start gap-3">
                  <div className="shrink-0 mt-0.5">
                    {!n.is_read && <span className="w-2 h-2 rounded-full bg-teal-500 inline-block" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900">{n.title}</p>
                    <p className="text-sm text-slate-500 mt-0.5">{n.message}</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                    </p>
                  </div>
                  {!n.is_read && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => { e.preventDefault(); handleMarkRead(n); }}
                      className="shrink-0"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </Card>
            );
            return link ? (
              <Link key={n.id || n._id} to={link} onClick={() => handleMarkRead(n)}>
                {content}
              </Link>
            ) : (
              <div key={n.id || n._id}>{content}</div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
