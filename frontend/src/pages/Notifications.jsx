import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bell, Check, CheckCheck, ChevronRight, ExternalLink } from 'lucide-react';
import { notificationsApi } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';
import { formatLongWeekdayDateIst, formatTimeIst } from '../lib/istTime';

function getLink(notification) {
  const type = notification.related_entity_type;
  const id = notification.related_entity_id;
  if (!id) return null;
  if (type === 'rfq') return `/rfq/${id}`;
  if (type === 'order') return `/orders/${id}`;
  if (type === 'user') return `/suppliers/${id}`;
  return null;
}

function dayKey(ts) {
  if (!ts) return 'Unknown date';
  return formatLongWeekdayDateIst(ts) || 'Unknown date';
}

export default function Notifications() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const load = () => {
    notificationsApi
      .getMe()
      .then((r) => {
        setList(r.data.data?.notifications || []);
      })
      .catch(() => setList([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(), []);

  const grouped = useMemo(() => {
    const m = new Map();
    for (const n of list) {
      const k = dayKey(n.created_at);
      if (!m.has(k)) m.set(k, []);
      m.get(k).push(n);
    }
    return m;
  }, [list]);

  const handleMarkRead = (n) => {
    if (n.is_read) return;
    notificationsApi.markRead(n.id || n._id).then(() => load()).catch(() => toast.add('Failed to mark as read', 'error'));
  };

  const handleMarkAllRead = () => {
    notificationsApi
      .markAllRead()
      .then(() => {
        load();
        toast.add('All marked as read', 'success');
      })
      .catch(() => toast.add('Failed', 'error'));
  };

  if (loading) {
    return (
      <div className="space-y-4 max-w-2xl">
        <div className="h-10 w-56 bg-slate-200 rounded-xl animate-pulse" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-slate-100 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 max-w-2xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="section-heading mb-1">Inbox</p>
          <h1 className="page-heading flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-100 text-teal-700">
              <Bell className="h-6 w-6" />
            </span>
            Notifications
          </h1>
          <p className="text-sm text-slate-500 mt-2">RFQ, order, and account updates. Unread items stay highlighted.</p>
        </div>
        {list.length > 0 && list.some((n) => !n.is_read) && (
          <Button variant="secondary" size="sm" onClick={handleMarkAllRead} className="gap-2 rounded-xl shrink-0">
            <CheckCheck className="h-4 w-4" /> Mark all read
          </Button>
        )}
      </div>

      {list.length === 0 ? (
        <EmptyState title="No notifications" description="You're all caught up — we'll surface RFQ and order events here." />
      ) : (
        <div className="space-y-10">
          {[...grouped.entries()].map(([day, items]) => (
            <div key={day}>
              <p className="section-heading mb-4 pl-1">{day}</p>
              <div className="space-y-3">
                {items.map((n, i) => {
                  const link = getLink(n);
                  const inner = (
                    <Card
                      className={`transition-all border-slate-200/90 ${
                        n.is_read
                          ? 'bg-slate-50/40 opacity-90'
                          : 'bg-white border-l-4 border-l-teal-500 shadow-lg shadow-teal-900/5 ring-1 ring-teal-100/50'
                      }`}
                    >
                      <div className="p-4 sm:p-5 flex items-start gap-4">
                        <div className="shrink-0 pt-1">
                          {!n.is_read ? (
                            <span className="flex h-2.5 w-2.5 rounded-full bg-teal-500 shadow-sm shadow-teal-500/50" title="Unread" />
                          ) : (
                            <span className="flex h-2.5 w-2.5 rounded-full bg-slate-200" title="Read" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className={`font-semibold ${n.is_read ? 'text-slate-700' : 'text-slate-900'}`}>{n.title ?? 'Notification'}</p>
                            {!n.is_read && (
                              <Badge variant="teal" className="text-[10px] font-bold">
                                New
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-slate-500 mt-1 leading-relaxed">{n.message ?? '—'}</p>
                          <p className="text-xs text-slate-400 mt-3 font-medium tabular-nums">
                            {n.created_at ? formatTimeIst(n.created_at) : ''}
                          </p>
                          {link && (
                            <span className="inline-flex items-center gap-1 mt-3 text-sm font-semibold text-teal-600">
                              Open related page <ChevronRight className="h-4 w-4" />
                            </span>
                          )}
                        </div>
                        <div className="flex flex-col gap-2 shrink-0">
                          {!n.is_read && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                handleMarkRead(n);
                              }}
                              className="rounded-lg"
                              title="Mark read"
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          )}
                          {link && (
                            <span className="hidden sm:inline-flex text-slate-300" aria-hidden>
                              <ExternalLink className="h-4 w-4" />
                            </span>
                          )}
                        </div>
                      </div>
                    </Card>
                  );
                  return link ? (
                    <motion.div
                      key={n.id || n._id || i}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.03 }}
                    >
                      <Link to={link} onClick={() => handleMarkRead(n)} className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 rounded-2xl">
                        {inner}
                      </Link>
                    </motion.div>
                  ) : (
                    <motion.div
                      key={n.id || n._id || i}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.03 }}
                    >
                      {inner}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
