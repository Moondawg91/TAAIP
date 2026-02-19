import React from 'react'
import { Box, Typography } from '@mui/material'

export default function HelpDeskLandingPage(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">Help Desk</Typography>
      <Typography sx={{ mt:2, color:'text.secondary' }}>Submit requests and browse the knowledge base.</Typography>
    </Box>
  )
}
