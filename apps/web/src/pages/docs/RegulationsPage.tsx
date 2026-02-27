import React from 'react'
import { Box, Typography } from '@mui/material'
import EmptyState from '../../components/EmptyState'

export default function DocsRegulations(){
  return (
    <Box>
      <Typography variant="h4">Regulations & Messages</Typography>
      <Box sx={{ mt:2 }}>
        <EmptyState title="Regulations" subtitle="Regulatory documents and messages will appear here." />
      </Box>
    </Box>
  )
}
