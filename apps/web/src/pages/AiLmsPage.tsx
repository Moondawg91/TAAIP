import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'
import DashboardLayout from '../components/DashboardLayout'

export default function AiLmsPage(){
  return (
    <DashboardLayout filters={<div/>} kpis={<div/>}>
      <Box>
        <Typography variant="h5">AI-LMS</Typography>
        <Card sx={{mt:2}}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Recommendations and narrative insights will appear here.</Typography>
          </CardContent>
        </Card>
      </Box>
    </DashboardLayout>
  )
}
