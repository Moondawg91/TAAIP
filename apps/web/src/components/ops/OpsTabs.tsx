import React from 'react'
import { Tabs, Tab, Box } from '@mui/material'

export default function OpsTabs({ active, onChange }: { active: 'planning'; onChange: (t:'planning')=>void }){
  return (
    <Box>
      <Tabs value={0} onChange={(_,v)=> onChange('planning')}>
        <Tab label="Planning & Events" />
      </Tabs>
    </Box>
  )
}
