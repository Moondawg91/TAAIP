import React, { useEffect } from 'react'
import { Box, Typography, GlobalStyles } from '@mui/material'
import SectionSidebar from '../components/SectionSidebar'
import TopHeader from '../components/TopHeader'
import SystemStrip from '../components/SystemStrip'
import tokens from '../theme/tokens'

export default function ShellLayout({ children }: { children?: React.ReactNode }) {
  useEffect(()=>{
    try{ document.title = 'TAAIP' }catch(e){}
  },[])
  return (
    <Box sx={{ display: 'flex', height: '100vh', background: tokens.colors.frameBg }}>
      <GlobalStyles styles={{
        ':root': {
          '--taaip-font-size': '13px',
          '--taaip-panel-bg': '#0B0B10',
          '--taaip-panel-border': 'rgba(255,255,255,0.06)',
          '--taaip-panel-radius': '3px'
        },
        '.MuiContainer-root': {
          maxWidth: '100% !important',
          width: '100% !important',
          paddingLeft: '8px !important',
          paddingRight: '8px !important',
          minWidth: 0,
        },
        '.MuiContainer-maxWidthLg, .MuiContainer-maxWidthXl, .MuiContainer-maxWidthMd, .MuiContainer-maxWidthSm': {
          maxWidth: '100% !important'
        }
        ,
        // compact table and panel density overrides
        '.MuiTableCell-root': {
          padding: '6px 8px'
        },
        '.MuiTable-root thead th': {
          position: 'sticky',
          top: 0,
          background: 'rgba(11,11,16,0.9)'
        },
        '.MuiPaper-root': {
          background: 'transparent'
        }
      }} />
      <SectionSidebar />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
        <Box sx={{ background: tokens.colors.headerBg }}>
          <TopHeader />
        </Box>
        <SystemStrip />
        <Box component="main" sx={{ p: { xs: 1, md: 2 }, flex: 1, background: tokens.colors.canvasBg, width: '100%', minWidth: 0, overflow: 'auto' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: tokens.spacing.xs, width: '100%' }}>
            {children}
          </Box>
        </Box>
        <Box component="footer" sx={{ p:tokens.spacing.md, borderTop: `1px solid ${tokens.colors.borderSubtle}`, textAlign:'center', background: tokens.colors.frameBg }}>
          <Typography variant="caption" sx={{ color: tokens.colors.textSecondary }}>© 2026 TAAIP — Talent Acquisition Intelligence & Analytics Platform</Typography>
        </Box>
      </Box>
    </Box>
  )
}
