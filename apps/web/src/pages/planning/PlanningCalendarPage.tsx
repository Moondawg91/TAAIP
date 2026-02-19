import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function PlanningCalendarPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Calendar / Scheduling</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Planning calendar for projects and events.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Calendar</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>View and manage scheduled items.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
