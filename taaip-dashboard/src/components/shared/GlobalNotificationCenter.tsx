import React, { useEffect, useMemo, useState } from 'react';
import { Bell, BellOff } from 'lucide-react';
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  subscribeNotifications,
} from '../../lib/notifications/controller';
import { NotificationItem } from '../../lib/notifications/types';

function severityClass(severity: NotificationItem['severity']): string {
  if (severity === 'critical') return 'text-red-300 border-red-800 bg-red-950/40';
  if (severity === 'warning') return 'text-amber-300 border-amber-800 bg-amber-950/40';
  if (severity === 'success') return 'text-green-300 border-green-800 bg-green-950/40';
  return 'text-blue-200 border-blue-800 bg-blue-950/40';
}

export const GlobalNotificationCenter: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>(() => listNotifications());

  useEffect(() => subscribeNotifications(setItems), []);

  const unread = useMemo(() => items.filter((item) => !item.read).length, [items]);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative rounded border border-[#1D3A5C] bg-[#0B1F3A] px-2.5 py-1.5 text-xs text-[#CBD5E1] hover:bg-[#122A4A]"
      >
        <span className="inline-flex items-center gap-1.5">
          {unread > 0 ? <Bell className="h-3.5 w-3.5" /> : <BellOff className="h-3.5 w-3.5" />}
          Alerts
        </span>
        {unread > 0 && (
          <span className="absolute -right-2 -top-2 min-w-[18px] rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">
            {unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-[420px] max-h-[360px] overflow-auto rounded border border-[#1D3A5C] bg-[#081B33] p-3 shadow-2xl z-50">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-xs uppercase tracking-[0.08em] text-[#94A3B8]">Operational Alerts</div>
            <button
              onClick={() => markAllNotificationsRead()}
              className="text-[11px] text-[#93C5FD] hover:text-[#DBEAFE]"
            >
              Mark all read
            </button>
          </div>

          <div className="space-y-2">
            {items.length === 0 && <div className="text-xs text-[#64748B]">No alerts available.</div>}
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => markNotificationRead(item.id)}
                className={`w-full rounded border p-2 text-left ${severityClass(item.severity)} ${item.read ? 'opacity-60' : ''}`}
              >
                <div className="text-[11px] uppercase tracking-[0.08em]">{item.category}</div>
                <div className="mt-0.5 text-sm font-semibold">{item.title}</div>
                <div className="text-xs">{item.message}</div>
                <div className="mt-1 text-[10px] text-[#94A3B8]">{item.source} | {new Date(item.createdAt).toLocaleString()}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GlobalNotificationCenter;
