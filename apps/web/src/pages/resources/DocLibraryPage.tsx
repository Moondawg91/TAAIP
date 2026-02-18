import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function DocLibraryPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Document Library</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Centralized document repository and training materials.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Library</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Browse and search documents.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
