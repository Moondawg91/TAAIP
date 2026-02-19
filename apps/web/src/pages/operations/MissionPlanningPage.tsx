import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function MissionPlanningPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <DashboardToolbar title="Mission Planning" subtitle="Plan missions and assign resources" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert(`Export ${t} coming soon`) }} />
      <Typography variant="h5">Mission Planning</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Plan missions, assign resources, and track schedules.</Typography>

      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Plans</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Create and manage mission plans here.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
