import React from 'react'
import { Box, Typography, Card, CardContent, Chip } from '@mui/material'

export default function TargetingDataPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <div>
          <Typography variant="h5">Targeting Data</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Data sources and segmentation tools.</Typography>
        </div>
        <Chip label="Placeholder" sx={{ bgcolor:'background.paper', color:'text.primary' }} />
      </Box>

      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Placeholder for targeting datasets and filters.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
