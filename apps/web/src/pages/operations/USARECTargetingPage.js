import React from 'react'
import { Box, Typography, Paper } from '@mui/material'
import ZeroState from '../../components/ZeroState'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function USARECTargetingPage() {
  return (
    <Box sx={{ minHeight: '100%', p: 3, bgcolor: 'background.default', color: 'text.primary' }}>
      <DashboardToolbar title="USAREC Targeting" subtitle="Targeting methodology & datasets" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert('Export unavailable') }} />
      <Paper elevation={0} sx={{ p: 3, bgcolor: 'transparent', color: 'inherit' }}>
        <Typography variant="h4" sx={{ color: 'text.primary' }}>USAREC Targeting</Typography>
        <ZeroState title="Feature available soon" message="This route exists but is not enabled yet." />
      </Paper>
    </Box>
  )
}
