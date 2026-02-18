import React from 'react'
import { Box, Typography, Chip } from '@mui/material'

export default function TargetingBoardPage(){
  return (
    <Box>
      <Typography variant="h4">Targeting Board</Typography>
      <Chip label="Status: Coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
