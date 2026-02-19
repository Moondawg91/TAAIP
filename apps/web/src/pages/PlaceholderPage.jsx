import React from 'react'
import { Box, Typography, Button } from '@mui/material'

export default function PlaceholderPage({ title = 'Coming Soon', subtitle = 'This page is wired and ready for future implementation.' }) {
  return (
    <Box sx={{ minHeight: '100vh', px: 4, py: 6, bgcolor: 'background.default', color: 'text.primary', display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
        <Typography variant="subtitle1" sx={{ color: 'text.secondary', mt: 1 }}>{subtitle}</Typography>
      </Box>

      <Box sx={{ mt: 4, p:3, borderRadius: 2, bgcolor: 'background.paper', color: 'text.primary', maxWidth: 720 }}>
        <Typography variant="h6" sx={{ fontWeight:600 }}>Status: Coming soon</Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary', mt: 1 }}>This page is a placeholder to ensure navigation works and maintain the dark UI. Implement Phase features here when ready.</Typography>
      </Box>

      <Box sx={{ flex:1 }} />

      <Box>
        <Button variant="contained" color="primary" href="#" onClick={(e)=>e.preventDefault()}>Acknowledged</Button>
      </Box>
    </Box>
  )
}
