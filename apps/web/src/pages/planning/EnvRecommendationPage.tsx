import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function EnvRecommendationPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Enabler Recommendations</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Recommendations from the environmental recommendation engine.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Recommendations</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Suggested enablers and next steps.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
