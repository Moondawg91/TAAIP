import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'
import DashboardLayout from '../components/DashboardLayout'

export default function IngestPage(){
  return (
    <DashboardLayout filters={<div/>} kpis={<div/>}>
      <Box>
        <Typography variant="h5">Ingest / Data</Typography>
        <Card sx={{mt:2}}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Upload status and pipeline health will appear here.</Typography>
          </CardContent>
        </Card>
      </Box>
    </DashboardLayout>
  )
}
