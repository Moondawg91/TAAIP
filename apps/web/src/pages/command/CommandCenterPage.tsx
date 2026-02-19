import React from 'react'
import { Box, Typography, Chip } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function CommandCenterPage(){
  return (
    <Box>
      <DashboardToolbar title="420T Command Center" subtitle="Central hub for operational command & control." filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert(`Export ${t} coming soon`) }} />
      <Typography variant="body2" color="text.secondary">Central hub for operational command & control.</Typography>
      <Chip label="Status: Available" color="success" sx={{ mt:2 }} />
    </Box>
  )
}
