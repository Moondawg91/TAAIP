import React from 'react'
import { Box, Typography } from '@mui/material'

export default function EventPerformancePage(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">Event Performance</Typography>
      <Typography sx={{ mt:2, color:'text.secondary' }}>Event performance metrics and reporting.</Typography>
    </Box>
  )
}
