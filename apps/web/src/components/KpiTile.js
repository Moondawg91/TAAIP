import React from 'react'
import {Card, CardContent, Typography, Box} from '@mui/material'

export default function KpiTile({title, value, sub}){
  return (
    <Card variant="outlined" sx={{minWidth:120}}>
      <CardContent>
        <Typography variant="caption" color="text.secondary">{title}</Typography>
        <Box sx={{display:'flex', alignItems:'baseline', gap:1}}>
          <Typography variant="h5">{value !== undefined && value !== null ? String(value) : 'N/A'}</Typography>
        </Box>
        {sub && <Typography variant="caption" color="text.secondary">{sub}</Typography>}
      </CardContent>
    </Card>
  )
}
