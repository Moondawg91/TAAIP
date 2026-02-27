import React from 'react'
import { Box, Paper, Typography, Button } from '@mui/material'

type Props = {
  title?: string
  message?: string
  actionLabel?: string
  actionHref?: string
}

export default function ZeroState({ title, message, actionLabel, actionHref }: Props){
  return (
    <Paper sx={{ p:2, mb:2, bgcolor: 'transparent', borderRadius: '4px', border: '1px dashed rgba(255,255,255,0.04)' }} elevation={0}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:2 }}>
        <Box>
          <Typography variant="h6">{title || 'No records yet'}</Typography>
          { message ? <Typography variant="body2" sx={{ color: 'text.secondary', mt:0.5 }}>{message}</Typography> : null }
        </Box>
        { actionLabel ? (
          <Button size="small" variant="contained" href={actionHref} sx={{ borderRadius: '4px' }}>{actionLabel}</Button>
        ) : null }
      </Box>
    </Paper>
  )
}
