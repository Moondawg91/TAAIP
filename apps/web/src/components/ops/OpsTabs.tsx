import React from 'react'
import { Tabs, Tab, Box } from '@mui/material'

export default function OpsTabs({ active, onChange }: { active: 'planning'|'fusion'|'roi'; onChange: (t:'planning'|'fusion'|'roi')=>void }){
  const idx = active === 'planning' ? 0 : active === 'fusion' ? 1 : 2
  return (
    <Box>
      <Tabs value={idx} onChange={(_,v)=> onChange(v===0?'planning':v===1?'fusion':'roi')}>
        <Tab label="Planning & Events" />
        <Tab label="TWG / Fusion Cell" />
        <Tab label="ROI & Funnel" />
      </Tabs>
    </Box>
  )
}
