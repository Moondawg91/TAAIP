import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'
import DashboardLayout from '../components/DashboardLayout'

export default function HelpDeskPage(){
  return (
    <DashboardLayout filters={<div/>} kpis={<div/>}>
      <Box>
        <Typography variant="h5">Help Desk</Typography>
        <Card sx={{mt:2}}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Help desk and support resources.</Typography>
          </CardContent>
        </Card>
      </Box>
    </DashboardLayout>
  )
}
