import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function CommunityEngagementPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Community Engagement</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Manage community outreach, partners, and events.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Engagements</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Track community events and engagement outcomes.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
