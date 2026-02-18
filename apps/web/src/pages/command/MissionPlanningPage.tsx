import React from 'react'
import { Box, Typography, Card, CardContent, Chip } from '@mui/material'

export default function MissionPlanningPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <div>
          <Typography variant="h5">Mission Planning</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Planning workspace for mission execution.</Typography>
        </div>
        <Chip label="Placeholder" sx={{ bgcolor:'background.paper', color:'text.primary' }} />
      </Box>

      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>This page is a placeholder for Mission Planning tools and timelines.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
