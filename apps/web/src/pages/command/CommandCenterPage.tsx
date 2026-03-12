import React from 'react'
import { Box, Typography, Chip, Button, Stack } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function CommandCenterPage(){
  return (
    <Box>
      <DashboardToolbar title="420T Command Center" subtitle="Central hub for operational command & control." filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert('Export unavailable') }} />
      <Typography variant="body2" color="text.secondary">Central hub for operational command & control.</Typography>
      <Chip label="Status: Available" color="success" sx={{ mt:2 }} />

      <Stack direction="row" spacing={2} sx={{ mt:2 }}>
        <Button variant="contained" color="primary" href="/command-center/420t">Open 420T Command Center</Button>
        <Button variant="outlined" color="primary" href="/command-center/mdmp">Open MDMP Workspace</Button>
      </Stack>
    </Box>
  )
}
