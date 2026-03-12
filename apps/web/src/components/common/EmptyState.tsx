import React from 'react'
import { Box, Typography, Link, Button } from '@mui/material'

type EmptyStateProps = {
  title?: string
  subtitle?: string
  actionLabel?: string
  onAction?: () => void
}

export default function EmptyState({ title='No data yet', subtitle='Data not loaded. Load datasets in Data Hub.', actionLabel='', onAction }: EmptyStateProps){
  return (
    <Box sx={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', p:4, bgcolor:'transparent', color:'text.secondary', borderRadius:1 }}>
      <Typography variant="h6" sx={{ color: 'text.primary', mb:1 }}>{title}</Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary', mb:2 }}>{subtitle}</Typography>
      {actionLabel ? (
        onAction ? (
          <Button variant="contained" onClick={onAction}>{actionLabel}</Button>
        ) : (
          <Button variant="contained" disabled>{actionLabel}</Button>
        )
      ) : null}
    </Box>
  )
}
