import React from 'react'
import { Box, Typography, List, ListItem } from '@mui/material'
import { useTheme } from '@mui/material/styles'

export default function VirtualTechnicianBrief(){
  const theme = useTheme()
  const panelBg = theme.palette.mode === 'dark' ? 'background.paper' : '#0f1720'
  // Empty-safe brief
  const watching: string[] = []
  const checks: string[] = []
  // Optional system metadata (if available later)
  const mode = null
  const dataAsOf = null
  const alertsCount = null

  return (
    <Box sx={{ p:2, bgcolor: panelBg, borderRadius: '4px' }}>
      <Typography variant="h6" sx={{ mb:1 }}>Virtual Technician Brief</Typography>

      <Box sx={{ mb:1 }}>
        <Typography variant="subtitle2">What I’m watching</Typography>
        {watching.length === 0 ? (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>No items tracked.</Typography>
        ) : (
          <List dense>
            {watching.map((w,i)=> <ListItem key={i} sx={{ py:0 }}>{w}</ListItem>)}
          </List>
        )}
      </Box>

      <Box sx={{ mb:1 }}>
        <Typography variant="subtitle2">Recommended next checks</Typography>
        {checks.length === 0 ? (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>No recommendations.</Typography>
        ) : (
          <List dense>
            {checks.map((c,i)=> <ListItem key={i} sx={{ py:0 }}>{c}</ListItem>)}
          </List>
        )}
      </Box>

      {(mode || dataAsOf || alertsCount !== null) && (
        <Box sx={{ mt:1 }}>
          {mode && <Typography variant="caption">Mode: {mode}</Typography>}
          {dataAsOf && <Typography variant="caption" sx={{ display:'block' }}>Data As Of: {dataAsOf}</Typography>}
          {alertsCount !== null && <Typography variant="caption" sx={{ display:'block' }}>Alerts: {alertsCount}</Typography>}
        </Box>
      )}
    </Box>
  )
}
