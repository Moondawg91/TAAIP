import { createTheme } from '@mui/material/styles'
import { alpha } from '@mui/material'

const palette = {
  mode: 'dark' as const,
  background: {
    default: '#0b0f1e',
    paper: '#121833'
  },
  primary: { main: '#7c3aed', contrastText: '#EDEDF7' },
  secondary: { main: '#f97316', contrastText: '#0b0f1e' },
  info: { main: '#38bdf8' },
  text: { primary: '#EDEDF7', secondary: alpha('#EDEDF7', 0.8) },
  divider: 'rgba(255,255,255,0.08)'
}

const muiTheme = createTheme({
  palette,
  shape: { borderRadius: 2 },
  typography: { h6: { fontWeight: 700 }, button: { textTransform: 'none' } },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: palette.background.default,
          backgroundImage: 'linear-gradient(180deg, rgba(124,77,255,0.04), transparent)',
          backgroundAttachment: 'fixed'
        },
        '::-webkit-scrollbar': { width: 8, height:8 },
        '::-webkit-scrollbar-thumb': { background: alpha('#7C4DFF', 0.22), borderRadius: 8 }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: `linear-gradient(90deg, ${alpha('#7C4DFF',0.12)}, transparent)`,
          borderBottom: `1px solid ${palette.divider}
`
        }
      }
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: palette.background.paper,
          color: palette.text.primary,
          border: `1px solid ${palette.divider}`,
          borderRadius: 2
        }
      }
    },
    MuiCard: { styleOverrides: { root: { backgroundColor: palette.background.paper, boxShadow: '0 4px 18px rgba(7,5,15,0.45)', borderRadius: 2 } } },
    MuiDrawer: { styleOverrides: { paper: { backgroundColor: palette.background.paper } } },
    MuiMenu: { styleOverrides: { paper: { backgroundColor: palette.background.paper } } },
    MuiListItemButton: { styleOverrides: { root: { borderRadius: 2, '&.Mui-selected': { background: alpha('#7C4DFF', 0.12), boxShadow: `0 6px 18px ${alpha('#7C4DFF',0.12)}`, border: `1px solid ${alpha('#7C4DFF',0.18)}` } } } },
    MuiTooltip: { styleOverrides: { tooltip: { backgroundColor: '#1b122f', color: '#EDEDF7', fontSize: 12 } } },
    MuiButton: { styleOverrides: { root: { borderRadius: 2 } } },
    MuiSelect: { styleOverrides: { root: { borderRadius: 2 } } },
    MuiTextField: { styleOverrides: { root: { borderRadius: 2 } } }
  }
})

export default muiTheme
