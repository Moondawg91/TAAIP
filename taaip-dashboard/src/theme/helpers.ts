import { colors } from './tokens';

export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(' ');
}

export function kpiGridTemplate(count: number) {
  const normalized = Math.min(6, Math.max(3, count));
  return `repeat(${normalized}, minmax(0, 1fr))`;
}

export function statusColor(status: 'default' | 'success' | 'warning' | 'danger' | 'accent' = 'default') {
  switch (status) {
    case 'success':
      return colors.successGreen;
    case 'warning':
      return colors.warningAmber;
    case 'danger':
      return colors.dangerRed;
    case 'accent':
      return colors.accentBlue;
    default:
      return colors.white;
  }
}
