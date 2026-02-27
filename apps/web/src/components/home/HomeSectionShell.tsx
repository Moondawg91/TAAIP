import React from 'react'
import { Box, Typography, Button } from '@mui/material'

export default function HomeSectionShell({ title, children }: { title: string; children?: React.ReactNode }){
  return (
    <Box sx={{ p:2, bgcolor: 'background.paper', borderRadius: '4px' }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', mb:1 }}>
        <Typography variant="h6">{title}</Typography>
      </Box>
      <Box>
        {children}
      </Box>
    </Box>
  )
}
