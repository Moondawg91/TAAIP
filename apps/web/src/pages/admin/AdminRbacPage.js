import React from 'react'
import { Box, Typography } from '@mui/material'

export default function AdminRbacPage(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">RBAC Administration</Typography>
      <Typography sx={{ mt:2, color:'text.secondary' }}>Manage roles, echelons, and user access here.</Typography>
    </Box>
  )
}
