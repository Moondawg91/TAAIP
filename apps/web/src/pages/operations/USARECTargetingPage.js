import React from 'react'
import { Box, Typography, Paper } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function USARECTargetingPage() {
  return (
    <Box sx={{ minHeight: '100%', p: 3, bgcolor: 'background.default', color: 'text.primary' }}>
      <DashboardToolbar title="USAREC Targeting" subtitle="Targeting methodology & datasets" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert(`Export ${t} coming soon`) }} />
      <Paper elevation={0} sx={{ p: 3, bgcolor: 'transparent', color: 'inherit' }}>
        <Typography variant="h4" sx={{ color: 'text.primary' }}>USAREC Targeting</Typography>
        <Typography variant="h6" sx={{ mt: 2, color: 'text.secondary' }}>Coming soon</Typography>
        <Typography sx={{ mt: 1, color: 'text.secondary' }}>
          This section will host USAREC targeting methodology, guidance, and datasets.
        </Typography>
      </Paper>
    </Box>
  )
}
