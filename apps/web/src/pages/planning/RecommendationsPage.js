import React from 'react'
import { Box, Typography } from '@mui/material'

export default function RecommendationsPage(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">COA / Recommendations</Typography>
      <Typography sx={{ mt:2, color:'text.secondary' }}>System-generated outputs and recommendations will appear here.</Typography>
    </Box>
  )
}
