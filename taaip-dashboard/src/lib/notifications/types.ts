export type NotificationCategory =
  | 'system'
  | 'ingestion'
  | 'document'
  | 'deadline'
  | 'targeting'
  | 'tor'
  | 'maintenance';

export type NotificationSeverity = 'info' | 'warning' | 'critical' | 'success';

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: NotificationCategory;
  severity: NotificationSeverity;
  createdAt: string;
  read: boolean;
  source: string;
}
