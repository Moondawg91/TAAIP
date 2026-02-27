import { createTheme } from '@mui/material/styles'
import { alpha } from '@mui/material'
import tokens from './tokens'

const palette = {
  mode: 'light' as const,
  background: {
    // canvas uses token for the app background
    default: tokens.colors.canvasBg,
    // paper used for elevated surfaces (cards)
    paper: tokens.colors.surface
  },
  primary: { main: tokens.colors.accentProponent, contrastText: tokens.colors.textPrimary },
  secondary: { main: '#0B3A66', contrastText: '#FFFFFF' },
  info: { main: tokens.colors.accentInfo },
  text: { primary: tokens.colors.textPrimary, secondary: tokens.colors.textSecondary },
  divider: alpha(tokens.colors.borderSubtle, 1)
}

const muiTheme = createTheme({
  palette,
  shape: { borderRadius: tokens.radius },
  typography: {
    h4: { fontWeight: 700, fontSize: '1.4rem' },
    h5: { fontWeight: 700, fontSize: '1.2rem' },
    h6: { fontWeight: 700 },
    button: { textTransform: 'none' }
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: palette.background.default,
          backgroundImage: 'none',
          backgroundAttachment: 'fixed',
          color: tokens.colors.textPrimary
        },
        '::-webkit-scrollbar': { width: 8, height:8 },
        '::-webkit-scrollbar-thumb': { background: alpha(tokens.colors.accentProponent, 0.22), borderRadius: 8 }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: `linear-gradient(90deg, ${alpha(tokens.colors.accentProponent,0.12)}, transparent)`,
          borderBottom: `1px solid ${palette.divider}`
        }
      }
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: tokens.colors.surface,
          color: tokens.colors.textPrimary,
          border: `1px solid ${tokens.colors.borderSubtle}`,
          borderRadius: tokens.radius
        }
      }
    },
    MuiCard: { styleOverrides: { root: { backgroundColor: tokens.colors.surface, boxShadow: '0 8px 28px rgba(6,10,18,0.12)', borderRadius: tokens.radius } } },
    MuiDrawer: { styleOverrides: { paper: { backgroundColor: palette.background.paper } } },
    MuiMenu: { styleOverrides: { paper: { backgroundColor: palette.background.paper } } },
    MuiListItemButton: { styleOverrides: { root: { borderRadius: tokens.radius, '&.Mui-selected': { background: alpha(tokens.colors.accentProponent, 0.08), boxShadow: `0 6px 18px ${alpha(tokens.colors.accentProponent,0.08)}`, border: `1px solid ${alpha(tokens.colors.accentProponent,0.12)}` } } } },
    MuiTooltip: { styleOverrides: { tooltip: { backgroundColor: '#1b122f', color: '#EDEDF7', fontSize: 12 } } },
    MuiButton: { styleOverrides: { root: { borderRadius: tokens.radius } } },
    MuiSelect: { styleOverrides: { root: { borderRadius: tokens.radius, backgroundColor: tokens.colors.surface, color: tokens.colors.textPrimary } } },
    MuiTextField: { styleOverrides: { root: { borderRadius: tokens.radius, backgroundColor: tokens.colors.surface, color: tokens.colors.textPrimary } } }
  }
})

export default muiTheme
