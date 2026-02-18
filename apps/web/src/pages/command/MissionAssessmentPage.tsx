import React, { useState } from 'react'
import { Box, Typography, Tabs, Tab, Card, CardContent, Grid, Chip } from '@mui/material'

function TabPanel({ children, value, index }: any){
  return value === index ? <Box sx={{ mt:2 }}>{children}</Box> : null
}

export default function MissionAssessmentPage(){
  const [tab, setTab] = useState(0)
  return (
    <Box sx={{ p:3, minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <div>
          <Typography variant="h5">Mission Assessment</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>FY / QTR / Month assessment for recruiting missions.</Typography>
        </div>
        <Chip label="Status: Placeholder" sx={{ bgcolor:'background.paper', color:'text.primary' }} />
      </Box>

      <Tabs value={tab} onChange={(_,v)=>setTab(v)} aria-label="assessment-tabs">
        <Tab label="FY" />
        <Tab label="Quarter" />
        <Tab label="Month" />
      </Tabs>

      <TabPanel value={tab} index={0}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor:'background.paper' }}>
              <CardContent>
                <Typography variant="h6">FY Summary</Typography>
                <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>No data yet. Use Mission Assessment to upload or link mission metrics.</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor:'background.paper' }}>
              <CardContent>
                <Typography variant="h6">Standards Baseline</Typography>
                <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Baseline metrics will appear here.</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tab} index={1}>
        <Card sx={{ bgcolor:'background.paper' }}>
          <CardContent>
            <Typography variant="h6">Quarter Assessment</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Placeholder for QTR analysis and notes.</Typography>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tab} index={2}>
        <Card sx={{ bgcolor:'background.paper' }}>
          <CardContent>
            <Typography variant="h6">Monthly Assessment</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Monthly performance and trends.</Typography>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  )
}
