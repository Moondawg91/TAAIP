import React from 'react'
import { Box, Typography, Card, CardContent, Button } from '@mui/material'

export default function NotLoadedPage({ title, subtitle }: { title: string; subtitle?: string }){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">{title || 'Not Loaded'}</Typography>
      {subtitle && <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>{subtitle}</Typography>}
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="body2" sx={{ color:'text.secondary', mb:1 }}>No operational datasets are available for this page. Load datasets in the Data Hub.</Typography>
          <a href="/data-hub" style={{ fontSize:13 }}>Data Hub</a>
        </CardContent>
      </Card>
    </Box>
  )
}

export { NotLoadedPage }
