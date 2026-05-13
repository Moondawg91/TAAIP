export type AuditEventType =
  | 'login'
  | 'page_access'
  | 'document_upload'
  | 'document_delete'
  | 'srp_rop_twg_change'
  | 'permission_change'
  | 'system_config_change';

export interface AuditRecord {
  id: string;
  eventType: AuditEventType;
  actor: string;
  message: string;
  target: string;
  timestamp: string;
  metadata?: Record<string, string | number | boolean>;
}
