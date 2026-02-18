import React from 'react'
import { Box, Typography, IconButton, Button } from '@mui/material'

type Props = {
  title: string
  icon?: React.ReactNode
  actionLabel?: string
  onActionClick?: () => void
  children?: React.ReactNode
}

export default function HomePanel({ title, icon, actionLabel, onActionClick, children }: Props){
  return (
    <Box sx={{ bgcolor: '#12121A', border: '1px solid #2A2A3A', borderRadius: 1, boxShadow: '0 2px 8px rgba(0,0,0,0.45)', p:2, color: '#EAEAF2' }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', mb:1 }}>
        <Box sx={{ display:'flex', alignItems:'center', gap:1 }}>
          {icon}
          <Typography variant="subtitle1" sx={{ fontWeight:700 }}>{title}</Typography>
        </Box>
        {actionLabel && (
          <Button size="small" variant="outlined" onClick={onActionClick} sx={{ color:'#EAEAF2', borderColor:'#2A2A3A' }}>{actionLabel}</Button>
        )}
      </Box>
      <Box>
        {children}
      </Box>
    </Box>
  )
}
