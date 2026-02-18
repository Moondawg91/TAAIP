import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function TicketStatusPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Ticket Status</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>View status of submitted help desk tickets.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Tickets</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Recent tickets and statuses.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
