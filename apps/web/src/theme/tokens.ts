export const themeTokens = {
  colors: {
    // Light Power BI-like palette: light canvas, strong yellow accent
    frameBg: '#FFFFFF',
    headerBg: '#F8F9FB',
    // Canvas is very light gray for contrast with white cards
    canvasBg: '#F4F6F9',
    // Card surface: white for clean charts and panels
    surface: '#FFFFFF',
    surfaceMuted: '#F1F5F9',
    // darker text for light backgrounds
    textPrimary: '#0F1724',
    textSecondary: '#475569',
    borderSubtle: '#E6EEF6',

    accentInfo: '#2F6FED',
    accentSuccess: '#1F8F4C',
    // Power BI yellow as primary accent
    accentWarning: '#FFB900',
    accentDanger: '#C2352A',
    // primary brand accent (use warm yellow)
    accentProponent: '#FFB900'
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32
  },
  // Less rounded for a more command-level feel
  radius: 2
}

export default themeTokens
