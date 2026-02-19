import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function ResourcesRegulationsPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Regulations</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Regulatory guidance and compliance documents.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Regulations</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Reference materials and regulatory text.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
