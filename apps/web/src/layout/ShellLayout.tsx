import React, { useEffect } from 'react'
import { Box, Typography, GlobalStyles } from '@mui/material'
import SectionSidebar from '../components/SectionSidebar'
import TopHeader from '../components/TopHeader'
import SystemStrip from '../components/SystemStrip'
import TopFilterBar from '../components/TopFilterBar'
import useRoutePolicy from '../auth/useRoutePolicy'
import tokens from '../theme/tokens'

export default function ShellLayout({ children }: { children?: React.ReactNode }) {
  useEffect(()=>{
    try{ document.title = 'TAAIP' }catch(e){}
  },[])
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', background: tokens.colors.frameBg }}>
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
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Box sx={{ background: tokens.colors.headerBg }}>
          <TopHeader />
        </Box>
        <SystemStrip />
        {/* Centralized top filter bar for dashboard pages */}
        {(() => {
          try {
            const rp = useRoutePolicy()
            if (rp && rp.showTopFilters) return <TopFilterBar />
          } catch (e) { }
          return null
        })()}
        <Box component="main" sx={{ p: { xs: 1, md: 1 }, flex: 1, background: tokens.colors.canvasBg, width: '100%', minWidth: 0, overflowY: 'auto' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: tokens.spacing.xs, width: '100%' }}>
            {children}
          </Box>
        </Box>
        {/* Footer removed from default shell to avoid persistent bottom spacing. Render per-page if needed. */}
      </Box>
    </Box>
  )
}
