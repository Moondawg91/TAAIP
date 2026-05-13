import React, { createContext, useContext, useMemo } from 'react';
import { themeTokens, type TAAIPThemeTokens } from './tokens';

interface ThemeContextValue {
  theme: TAAIPThemeTokens;
}

const ThemeContext = createContext<ThemeContextValue>({ theme: themeTokens });

const rootVars = {
  '--taaip-color-primaryNavy': themeTokens.colors.primaryNavy,
  '--taaip-color-accentBlue': themeTokens.colors.accentBlue,
  '--taaip-color-white': themeTokens.colors.white,
  '--taaip-color-slateGray': themeTokens.colors.slateGray,
  '--taaip-color-successGreen': themeTokens.colors.successGreen,
  '--taaip-color-warningAmber': themeTokens.colors.warningAmber,
  '--taaip-color-dangerRed': themeTokens.colors.dangerRed,
  '--taaip-space-xs': themeTokens.spacing.xs,
  '--taaip-space-sm': themeTokens.spacing.sm,
  '--taaip-space-md': themeTokens.spacing.md,
  '--taaip-space-lg': themeTokens.spacing.lg,
  '--taaip-space-xl': themeTokens.spacing.xl,
  '--taaip-radius-sm': themeTokens.radius.sm,
  '--taaip-radius-md': themeTokens.radius.md,
  '--taaip-font-family': themeTokens.typography.fontFamily,
  '--taaip-font-size-h1': themeTokens.typography.h1.fontSize,
  '--taaip-font-size-h2': themeTokens.typography.h2.fontSize,
  '--taaip-font-size-h3': themeTokens.typography.h3.fontSize,
  '--taaip-font-size-body': themeTokens.typography.body.fontSize,
  '--taaip-font-size-table': themeTokens.typography.table.fontSize,
} as React.CSSProperties;

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const value = useMemo(() => ({ theme: themeTokens }), []);

  return (
    <ThemeContext.Provider value={value}>
      <div style={rootVars} className="taaip-theme" data-theme="taaip-dark">
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
