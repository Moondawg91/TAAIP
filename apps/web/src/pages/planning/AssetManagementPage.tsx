import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'

export default function AssetManagementPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Asset Management</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Manage physical and digital assets used in operations.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Assets</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Inventory, assignment, and status tracking.</Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
