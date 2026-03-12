import React from 'react'
import { Box, Typography } from '@mui/material'

export default function Panel({ title, children, sx }:{ title?:string, children?:React.ReactNode, sx?:any }){
  return (
    <Box sx={{ border: '1px solid rgba(255,255,255,0.06)', borderRadius: '3px', bgcolor: 'transparent', overflow: 'hidden', ...sx }}>
      {title ? <Box sx={{ px:1, py:0.5, borderBottom: '1px solid rgba(255,255,255,0.03)' }}><Typography variant="subtitle2">{title}</Typography></Box> : null}
      <Box sx={{ p:1 }}>{children}</Box>
    </Box>
  )
}
