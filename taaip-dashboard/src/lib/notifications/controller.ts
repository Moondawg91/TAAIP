import { NotificationItem, NotificationCategory, NotificationSeverity } from './types';

type Listener = (items: NotificationItem[]) => void;

const listeners = new Set<Listener>();
let store: NotificationItem[] = [
  {
    id: 'boot-maintenance-window',
    title: 'Maintenance Window Scheduled',
    message: 'System maintenance scheduled for 0200-0300 UTC.',
    category: 'maintenance',
    severity: 'warning',
    createdAt: new Date().toISOString(),
    read: false,
    source: 'Admin Control',
  },
];

function emit(): void {
  const snapshot = [...store].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  listeners.forEach((listener) => listener(snapshot));
}

export function subscribeNotifications(listener: Listener): () => void {
  listeners.add(listener);
  listener([...store]);
  return () => {
    listeners.delete(listener);
  };
}

export function listNotifications(): NotificationItem[] {
  return [...store];
}

export function pushNotification(input: {
  title: string;
  message: string;
  category: NotificationCategory;
  severity?: NotificationSeverity;
  source: string;
}): NotificationItem {
  const item: NotificationItem = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: input.title,
    message: input.message,
    category: input.category,
    severity: input.severity ?? 'info',
    createdAt: new Date().toISOString(),
    read: false,
    source: input.source,
  };
  store = [item, ...store].slice(0, 200);
  emit();
  return item;
}

export function markNotificationRead(id: string): void {
  store = store.map((item) => (item.id === id ? { ...item, read: true } : item));
  emit();
}

export function markAllNotificationsRead(): void {
  store = store.map((item) => ({ ...item, read: true }));
  emit();
}

export function seedOperationalAlerts(): void {
  const now = new Date().toISOString();
  const seeds: NotificationItem[] = [
    {
      id: `seed-${Date.now()}-srp`,
      title: 'SRP Deadline Approaching',
      message: 'SRP package review due in 48 hours.',
      category: 'deadline',
      severity: 'warning',
      createdAt: now,
      read: false,
      source: 'SRP Engine',
    },
    {
      id: `seed-${Date.now()}-tor`,
      title: 'TOR Update Received',
      message: 'TOR doctrine references updated in Document Center.',
      category: 'tor',
      severity: 'info',
      createdAt: now,
      read: false,
      source: 'Document Center',
    },
  ];
  store = [...seeds, ...store].slice(0, 200);
  emit();
}
