import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function SystemStatusPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">System Status</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Current system health and uptime information.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Status</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Service statuses and recent incidents.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
