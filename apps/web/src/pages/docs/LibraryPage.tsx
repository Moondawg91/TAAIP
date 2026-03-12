import React from 'react'
import { Box, Typography } from '@mui/material'
import EmptyState from '../../components/EmptyState'

export default function DocsLibrary(){
  return (
    <Box>
      <Typography variant="h4">Document Library</Typography>
      <Box sx={{ mt:2 }}>
        <EmptyState title="Document Library" subtitle="Upload and organize documents in the Data Hub." />
      </Box>
    </Box>
  )
}
