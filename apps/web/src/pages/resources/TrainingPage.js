import React from 'react'
import { Box, Typography } from '@mui/material'

export default function TrainingPage(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">Training Modules</Typography>
      <Typography sx={{ mt:2, color:'text.secondary' }}>Training entry points and attendance management.</Typography>
    </Box>
  )
}
