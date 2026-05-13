import { AuditEventType, AuditRecord } from './types';

type AuditListener = (records: AuditRecord[]) => void;

const listeners = new Set<AuditListener>();
let records: AuditRecord[] = [];

function emit(): void {
  const snapshot = [...records].sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  listeners.forEach((listener) => listener(snapshot));
}

export function subscribeAuditRecords(listener: AuditListener): () => void {
  listeners.add(listener);
  listener([...records]);
  return () => listeners.delete(listener);
}

export function listAuditRecords(): AuditRecord[] {
  return [...records];
}

export function logAuditEvent(input: {
  eventType: AuditEventType;
  actor: string;
  message: string;
  target: string;
  metadata?: Record<string, string | number | boolean>;
}): AuditRecord {
  const record: AuditRecord = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    eventType: input.eventType,
    actor: input.actor,
    message: input.message,
    target: input.target,
    timestamp: new Date().toISOString(),
    metadata: input.metadata,
  };
  records = [record, ...records].slice(0, 5000);
  emit();
  return record;
}
