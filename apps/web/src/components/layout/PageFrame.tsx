import React from 'react'
import { Box } from '@mui/material'
import tokens from '../../theme/tokens'

export default function PageFrame({ children }: { children?: React.ReactNode }){
  return (
    <Box sx={{ width: '100%', minHeight: `calc(100vh - 112px)`, p: { xs:1, md:2 }, boxSizing: 'border-box' }}>
      {children}
    </Box>
  )
}
