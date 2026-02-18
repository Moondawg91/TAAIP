import React from 'react'
import { Box, Typography, Card, CardContent, Chip } from '@mui/material'

export default function USARECTargetingPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <div>
          <Typography variant="h5">USAREC Targeting Methodology</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Reference materials and methodological notes.</Typography>
        </div>
        <Chip label="Placeholder" sx={{ bgcolor:'background.paper', color:'text.primary' }} />
      </Box>

      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Methodology docs and guidance will be available here.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
