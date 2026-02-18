import React from 'react'
import { Box, Typography, Chip } from '@mui/material'

export default function CommandCenterPage(){
  return (
    <Box>
      <Typography variant="h4">420T Command Center</Typography>
      <Typography variant="body2" color="text.secondary">Central hub for operational command & control.</Typography>
      <Chip label="Status: Available" color="success" sx={{ mt:2 }} />
    </Box>
  )
}
