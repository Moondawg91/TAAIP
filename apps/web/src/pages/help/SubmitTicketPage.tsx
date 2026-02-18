import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function SubmitTicketPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Submit Ticket</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Create a help desk ticket for support.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Help Desk</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Provide details and submit a support request.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
