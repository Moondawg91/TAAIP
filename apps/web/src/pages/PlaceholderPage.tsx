import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function PlaceholderPage({ title, subtitle }: { title: string; subtitle?: string }){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">{title}</Typography>
      {subtitle && <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>{subtitle}</Typography>}
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>This page is a placeholder and will be implemented in Phase 2.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
