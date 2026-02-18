import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function TargetingMethodologyPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">USAREC Targeting Methodology</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Guidance and methodology for targeting.</Typography>

      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Methodology</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Document methodology, best practices, and references here.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
