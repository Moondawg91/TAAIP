import React from 'react'
import { Box, Typography, Chip } from '@mui/material'

export default function BudgetTrackerPage(){
  return (
    <Box>
      <Typography variant="h4">Budget Tracker</Typography>
      <Chip label="Status: Coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
