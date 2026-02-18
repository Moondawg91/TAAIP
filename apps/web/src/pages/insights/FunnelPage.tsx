import React from 'react'
import { Box, Typography, Chip } from '@mui/material'

export default function InsightsFunnel(){
  return (
    <Box>
      <Typography variant="h4">Recruiting Funnel</Typography>
      <Chip label="Status: Coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
