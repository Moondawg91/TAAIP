import React from 'react'
import { Box, Typography, Button } from '@mui/material'

export default function EmptyState({ title='Nothing here', subtitle='No data available', actionLabel, onAction }: { title?: string, subtitle?: string, actionLabel?: string, onAction?: ()=>void }){
  return (
    <Box sx={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', p:4, bgcolor:'transparent', color:'text.secondary', borderRadius:1 }}>
      <Typography variant="h6" sx={{ color: 'text.primary', mb:1 }}>{title}</Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary', mb:2 }}>{subtitle}</Typography>
      {actionLabel ? <Button variant="contained" onClick={onAction}>{actionLabel}</Button> : null}
    </Box>
  )
}
