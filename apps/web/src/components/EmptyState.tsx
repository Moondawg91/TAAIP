import React from 'react'
import { Box, Typography, Link } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'

export default function EmptyState({ title='No data loaded', subtitle='Load data in Data Hub.', children }:{ title?:string, subtitle?:string, children?:React.ReactNode }){
  const { hasPerm } = useAuth()
  const canViewDataHub = Boolean(hasPerm && (hasPerm('DATAHUB_READ') || hasPerm('datahub.read')))
  return (
    <Box sx={{ p:2, display:'flex', flexDirection:'column', alignItems:'center', gap:1 }}>
      <Typography variant="h6">{title}</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', textAlign:'center' }}>{subtitle}</Typography>
      {canViewDataHub && (
        <Typography variant="body2" sx={{ mt:1 }}>
          <Link href="/data-hub" underline="hover">Go to Data Hub</Link>
        </Typography>
      )}
      {children}
    </Box>
  )
}
