import React from 'react'
import { Box, Typography, Chip } from '@mui/material'

export default function InsightsCommandCenter(){
  return (
    <Box>
      <Typography variant="h4">Command Center</Typography>
      <Chip label="Status: Available" color="success" sx={{ mt:2 }} />
    </Box>
  )
}
