import React from 'react';
import { colors, radius, spacing, typography } from '../../theme/tokens';
import { cn, kpiGridTemplate, statusColor } from '../../theme/helpers';

interface AppShellProps {
  sidebar: React.ReactNode;
  header?: React.ReactNode;
  children: React.ReactNode;
  sidebarWidth?: number;
}

export const AppShell: React.FC<AppShellProps> = ({
  sidebar,
  header,
  children,
  sidebarWidth = 220,
}) => (
  <div
    className="min-h-screen"
    style={{
      backgroundColor: colors.primaryNavy,
      color: colors.white,
      fontFamily: typography.fontFamily,
    }}
  >
    <div className="fixed inset-y-0 left-0 z-30" style={{ width: `${sidebarWidth}px` }}>
      {sidebar}
    </div>
    <div className="flex min-h-screen flex-col" style={{ paddingLeft: `${sidebarWidth}px` }}>
      {header ? <header className="shrink-0">{header}</header> : null}
      <main className="flex-1" style={{ padding: spacing.lg }}>{children}</main>
    </div>
  </div>
);

// ─── Card ─────────────────────────────────────────────────────────────────────

interface CardProps {
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  noPad?: boolean;
}

export const Card: React.FC<CardProps> = ({ title, action, children, className = '', noPad }) => (
  <div
    className={cn('border', className)}
    style={{
      backgroundColor: colors.primaryNavy,
      borderColor: `${colors.slateGray}55`,
      borderRadius: radius.md,
    }}
  >
    {(title || action) && (
      <div
        className="flex items-center justify-between border-b"
        style={{
          paddingLeft: spacing.lg,
          paddingRight: spacing.lg,
          paddingTop: spacing.md,
          paddingBottom: spacing.md,
          borderColor: `${colors.slateGray}40`,
        }}
      >
        {title && (
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: colors.slateGray,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            {title}
          </span>
        )}
        {action && <div style={{ fontSize: '12px', color: colors.slateGray }}>{action}</div>}
      </div>
    )}
    <div style={noPad ? undefined : { padding: spacing.lg }}>{children}</div>
  </div>
);

// ─── KPIRow ───────────────────────────────────────────────────────────────────

interface KPIItem {
  label: string;
  value: string | number;
  sub?: string;
  color?: 'default' | 'success' | 'warning' | 'danger' | 'accent';
}

interface KPIRowProps {
  items: KPIItem[];
  className?: string;
}

export const KPIRow: React.FC<KPIRowProps> = ({ items, className = '' }) => (
  <div
    className={cn('grid gap-3', className)}
    style={{
      gap: spacing.md,
      gridTemplateColumns: kpiGridTemplate(items.length),
    }}
  >
    {items.map((kpi, i) => (
      <div
        key={i}
        className="border"
        style={{
          backgroundColor: colors.primaryNavy,
          borderColor: `${colors.slateGray}55`,
          borderRadius: radius.md,
          paddingLeft: spacing.lg,
          paddingRight: spacing.lg,
          paddingTop: spacing.md,
          paddingBottom: spacing.md,
        }}
      >
        <div
          style={{
            fontSize: '11px',
            color: colors.slateGray,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: spacing.xs,
          }}
        >
          {kpi.label}
        </div>
        <div
          style={{
            fontSize: '24px',
            fontWeight: 600,
            color: statusColor(kpi.color ?? 'default'),
            lineHeight: 1.2,
          }}
        >
          {kpi.value}
        </div>
        {kpi.sub && <div style={{ fontSize: '11px', color: colors.slateGray, marginTop: spacing.xs }}>{kpi.sub}</div>}
      </div>
    ))}
  </div>
);

// ─── Table ────────────────────────────────────────────────────────────────────

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  width?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
  selectedRow?: T | null;
  getRowId?: (row: T) => string;
  emptyText?: string;
}

export function Table<T extends Record<string, unknown>>({
  columns,
  rows,
  onRowClick,
  selectedRow,
  getRowId,
  emptyText = 'No data',
}: TableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full" style={{ fontSize: typography.table.fontSize, fontWeight: typography.table.fontWeight }}>
        <thead>
          <tr className="border-b" style={{ borderColor: `${colors.slateGray}55` }}>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className="text-left whitespace-nowrap"
                style={{
                  paddingLeft: spacing.md,
                  paddingRight: spacing.md,
                  paddingTop: spacing.sm,
                  paddingBottom: spacing.sm,
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.07em',
                  color: colors.slateGray,
                  ...(col.width ? { width: col.width } : {}),
                }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-center" style={{ padding: spacing.xl, color: colors.slateGray }}>{emptyText}</td>
            </tr>
          ) : (
            rows.map((row, i) => {
              const id = getRowId ? getRowId(row) : String(i);
              const isSelected = selectedRow && getRowId ? getRowId(selectedRow as T) === id : false;
              return (
                <tr
                  key={id}
                  onClick={() => onRowClick?.(row)}
                  className={cn('border-b transition-colors', onRowClick ? 'cursor-pointer' : '')}
                  style={{
                    borderColor: `${colors.slateGray}33`,
                    backgroundColor: isSelected ? `${colors.accentBlue}22` : 'transparent',
                  }}
                >
                  {columns.map((col) => (
                    <td
                      key={String(col.key)}
                      className="whitespace-nowrap"
                      style={{
                        paddingLeft: spacing.md,
                        paddingRight: spacing.md,
                        paddingTop: spacing.sm,
                        paddingBottom: spacing.sm,
                        color: colors.white,
                      }}
                    >
                      {col.render ? col.render(row) : String(row[col.key as keyof T] ?? '—')}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

// ─── Tabs ─────────────────────────────────────────────────────────────────────

interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, active, onChange }) => (
  <div className="flex gap-0 border-b" style={{ borderColor: `${colors.slateGray}55` }}>
    {tabs.map((tab) => (
      <button
        key={tab.id}
        onClick={() => onChange(tab.id)}
        className="border-b-2 whitespace-nowrap transition-colors"
        style={{
          paddingLeft: spacing.lg,
          paddingRight: spacing.lg,
          paddingTop: spacing.md,
          paddingBottom: spacing.md,
          fontSize: typography.body.fontSize,
          fontWeight: 600,
          borderColor: active === tab.id ? colors.accentBlue : 'transparent',
          color: active === tab.id ? colors.white : colors.slateGray,
        }}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// ─── RightDetailPanel ─────────────────────────────────────────────────────────

interface RightDetailPanelProps {
  title?: string;
  onClose?: () => void;
  children: React.ReactNode;
  width?: string;
  isOpen?: boolean;
}

export const RightDetailPanel: React.FC<RightDetailPanelProps> = ({
  title,
  onClose,
  children,
  width = '380px',
  isOpen = true,
}) => (
  <div
    className={cn(
      'flex flex-shrink-0 flex-col overflow-y-auto border-l transition-transform duration-300 ease-out',
      isOpen ? 'translate-x-0' : 'translate-x-full'
    )}
    style={{
      width,
      backgroundColor: colors.primaryNavy,
      borderColor: `${colors.slateGray}55`,
    }}
  >
    {(title || onClose) && (
      <div
        className="flex items-center justify-between border-b"
        style={{
          paddingLeft: spacing.lg,
          paddingRight: spacing.lg,
          paddingTop: spacing.md,
          paddingBottom: spacing.md,
          borderColor: `${colors.slateGray}55`,
        }}
      >
        {title && <span style={{ fontSize: typography.body.fontSize, fontWeight: 600, color: colors.white }}>{title}</span>}
        {onClose && (
          <button onClick={onClose} className="text-lg leading-none" style={{ color: colors.slateGray }}>&times;</button>
        )}
      </div>
    )}
    <div className="flex-1 overflow-y-auto" style={{ padding: spacing.lg }}>{children}</div>
  </div>
);

// ─── FilterBar ────────────────────────────────────────────────────────────────

interface FilterSelectProps {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}

export const FilterSelect: React.FC<FilterSelectProps> = ({ label, value, options, onChange }) => (
  <div className="flex flex-col" style={{ gap: '2px' }}>
    <label
      style={{
        fontSize: '10px',
        textTransform: 'uppercase',
        letterSpacing: '0.07em',
        color: colors.slateGray,
      }}
    >
      {label}
    </label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        backgroundColor: colors.primaryNavy,
        border: `1px solid ${colors.slateGray}55`,
        color: colors.white,
        fontSize: typography.table.fontSize,
        borderRadius: radius.sm,
        paddingLeft: spacing.sm,
        paddingRight: spacing.sm,
        paddingTop: spacing.xs,
        paddingBottom: spacing.xs,
      }}
    >
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  </div>
);

interface FilterBarProps {
  children: React.ReactNode;
}

export const FilterBar: React.FC<FilterBarProps> = ({ children }) => (
  <div
    className="flex flex-wrap items-end"
    style={{
      gap: spacing.lg,
      paddingLeft: spacing.lg,
      paddingRight: spacing.lg,
      paddingTop: spacing.md,
      paddingBottom: spacing.md,
      backgroundColor: colors.primaryNavy,
      border: `1px solid ${colors.slateGray}55`,
      borderRadius: radius.md,
    }}
  >
    {children}
  </div>
);

// ─── StatusBadge ──────────────────────────────────────────────────────────────

interface StatusBadgeProps {
  label: string;
  color?: string; // hex or token key
}

const badgePresets: Record<string, string> = {
  active:     'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30',
  approved:   'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30',
  'on track': 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30',
  completed:  'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30',
  planned:    'bg-[#1D4ED8]/20 text-[#1D4ED8] border-[#1D4ED8]/30',
  pending:    'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30',
  'at risk':  'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30',
  deferred:   'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30',
  modified:   'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30',
  'off track':'bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30',
  denied:     'bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30',
  cancelled:  'bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ label }) => {
  const preset = badgePresets[label?.toLowerCase()] ?? 'bg-[#081B33] text-[#64748B] border-[#64748B]';
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium border ${preset}`}>
      {label}
    </span>
  );
};

// ─── DetailSection ────────────────────────────────────────────────────────────

export const DetailSection: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div>
    <div
      className="border-b"
      style={{
        color: colors.slateGray,
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        marginBottom: spacing.sm,
        paddingBottom: spacing.xs,
        borderColor: `${colors.slateGray}55`,
      }}
    >
      {title}
    </div>
    {children}
  </div>
);

export const DetailRow: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="flex items-start justify-between" style={{ paddingTop: spacing.xs, paddingBottom: spacing.xs, fontSize: typography.table.fontSize }}>
    <span style={{ color: colors.slateGray, marginRight: spacing.lg, flexShrink: 0 }}>{label}</span>
    <span style={{ color: colors.white, textAlign: 'right' }}>{value}</span>
  </div>
);

// ─── PageShell ────────────────────────────────────────────────────────────────

interface PageShellProps {
  title: string;
  filters?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
}

export const PageShell: React.FC<PageShellProps> = ({ title, filters, actions, children }) => (
  <div className="flex flex-col h-full">
    <div className="mb-4">
      <div className="mb-3 flex items-center justify-between">
        <h1
          style={{
            fontSize: typography.h1.fontSize,
            fontWeight: typography.h1.fontWeight,
            color: colors.white,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          {title}
        </h1>
        {actions}
      </div>
      {filters ? <div>{filters}</div> : null}
    </div>
    {children}
  </div>
);

export type PerspectiveMode = 'operational' | 'analytical' | 'geospatial' | 'trend' | 'table';
export type VisualMode = 'kpi' | 'bar' | 'line' | 'scatter' | 'table' | 'heat';

const perspectiveTabs = [
  { id: 'operational', label: 'Operational' },
  { id: 'analytical', label: 'Analytical' },
  { id: 'geospatial', label: 'Geospatial' },
  { id: 'trend', label: 'Trend' },
  { id: 'table', label: 'Table' },
];

interface PerspectiveSelectorProps {
  value: PerspectiveMode;
  onChange: (value: PerspectiveMode) => void;
}

export const PerspectiveSelector: React.FC<PerspectiveSelectorProps> = ({ value, onChange }) => (
  <Tabs
    tabs={perspectiveTabs}
    active={value}
    onChange={(id) => onChange(id as PerspectiveMode)}
  />
);

const visualOptions: Array<{ id: VisualMode; label: string }> = [
  { id: 'kpi', label: 'KPI Grid' },
  { id: 'bar', label: 'Bar' },
  { id: 'line', label: 'Line' },
  { id: 'scatter', label: 'Scatter' },
  { id: 'heat', label: 'Heat Map' },
  { id: 'table', label: 'Table' },
];

interface VisualModeSwitchProps {
  value: VisualMode;
  onChange: (value: VisualMode) => void;
}

export const VisualModeSwitch: React.FC<VisualModeSwitchProps> = ({ value, onChange }) => (
  <div className="flex flex-wrap items-center gap-1">
    {visualOptions.map((opt) => (
      <button
        key={opt.id}
        onClick={() => onChange(opt.id)}
        className="rounded border px-2 py-0.5 text-[11px] font-semibold transition-colors"
        style={{
          borderColor: value === opt.id ? `${colors.accentBlue}AA` : `${colors.slateGray}55`,
          color: value === opt.id ? colors.white : colors.slateGray,
          backgroundColor: value === opt.id ? `${colors.accentBlue}33` : 'transparent',
        }}
      >
        {opt.label}
      </button>
    ))}
  </div>
);
