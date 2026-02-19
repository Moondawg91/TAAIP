import React from 'react'
import { Box, Typography, Chip } from '@mui/material'

export default function OpsEventsPage(){
  return (
    <Box>
      <Typography variant="h4">Event Management</Typography>
      <Chip label="Status: Coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
