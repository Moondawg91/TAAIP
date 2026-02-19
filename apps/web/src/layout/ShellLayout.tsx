import React from 'react'
import { Box, Typography } from '@mui/material'
import SectionSidebar from '../components/SectionSidebar'
import TopHeader from '../components/TopHeader'

export default function ShellLayout({ children }: { children?: React.ReactNode }) {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <SectionSidebar />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
        <TopHeader />
        <Box component="main" sx={{ p: 2, flex: 1 }}>
          <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
            {children}
          </Box>
        </Box>
        <Box component="footer" sx={{ p:2, borderTop: '1px solid rgba(255,255,255,0.04)', textAlign:'center' }}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>© 2026 TAAIP — Talent Acquisition Intelligence & Analytics Platform</Typography>
        </Box>
      </Box>
    </Box>
  )
}
