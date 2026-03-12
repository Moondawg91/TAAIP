import React from 'react'
import { Drawer, Box, Typography, Tabs, Tab } from '@mui/material'

export default function OpsDetailTray({ state, onClose }: any){
  if (!state) return null
  return (
    <Drawer anchor="bottom" open={state.open} onClose={onClose}>
      <Box sx={{ p:2, height: 360 }}>
        <Typography variant="h6">{state.title || 'Detail'}</Typography>
        <Tabs>
          <Tab label="Overview" />
          <Tab label="Notes" />
          <Tab label="Attachments" />
          <Tab label="History" />
        </Tabs>
        <Box sx={{ mt:2 }}>
          <Typography variant="body2">{JSON.stringify(state.payload || {}, null, 2)}</Typography>
        </Box>
      </Box>
    </Drawer>
  )
}
