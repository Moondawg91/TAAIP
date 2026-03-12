import React from 'react'
import { Box, Typography, List, ListItem, Link } from '@mui/material'
import { useTheme } from '@mui/material/styles'

const REFS = [
  '420T TOR (2026)', 'UR 601-73', 'UR 601-210', 'UM 3-0', 'UM 3-29', 'UM 3-30', 'UM 3-31', 'UM 3-32', 'UR 10-1', 'UR 27-4', 'UR 350-1', 'UR 350-13', 'UTP 3-10.2'
]

export default function ReferenceRails(){
  const theme = useTheme()
  const panelBg = theme.palette.mode === 'dark' ? 'background.paper' : '#0f1720'
  // App has a /docs/regulations route; if removed, change docsAvailable to false to show wiring note
  const docsAvailable = true
  return (
    <Box sx={{ p:2, bgcolor: panelBg, borderRadius: '4px' }}>
      <Typography variant="h6" sx={{ mb:1 }}>Reference Rails</Typography>
      <List dense disablePadding>
        {REFS.map(r => (
          <ListItem key={r} sx={{ py:0.5 }}>
            {docsAvailable ? (
              <Link href="/docs/regulations" underline="hover" sx={{ color: 'text.primary' }}>{r}</Link>
            ) : (
              <Typography variant="body2" sx={{ color: 'text.primary' }}>{r} <Typography component="span" variant="caption" sx={{ color: 'text.secondary' }}> — Docs wiring pending</Typography></Typography>
            )}
          </ListItem>
        ))}
      </List>
    </Box>
  )
}
