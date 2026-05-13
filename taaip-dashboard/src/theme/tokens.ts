export const colors = {
  primaryNavy: '#081B33',
  accentBlue: '#1D4ED8',
  white: '#F3F5F7',
  slateGray: '#64748B',
  successGreen: '#10B981',
  warningAmber: '#F59E0B',
  dangerRed: '#EF4444',
} as const;

export const typography = {
  fontFamily: 'Inter, sans-serif',
  h1: { fontSize: '24px', fontWeight: 600 },
  h2: { fontSize: '20px', fontWeight: 600 },
  h3: { fontSize: '16px', fontWeight: 600 },
  body: { fontSize: '14px', fontWeight: 400 },
  table: { fontSize: '13px', fontWeight: 400 },
} as const;

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '24px',
} as const;

export const radius = {
  sm: '4px',
  md: '6px',
} as const;

export const themeTokens = {
  colors,
  typography,
  spacing,
  radius,
} as const;

export type TAAIPThemeTokens = typeof themeTokens;
