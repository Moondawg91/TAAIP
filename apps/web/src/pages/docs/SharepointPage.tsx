import React from 'react'
import { Box, Typography } from '@mui/material'
import EmptyState from '../../components/EmptyState'

export default function DocsSharepoint(){
  return (
    <Box>
      <Typography variant="h4">SharePoint Files</Typography>
      <Box sx={{ mt:2 }}>
        <EmptyState title="SharePoint Files" subtitle="Connect SharePoint sources via the Data Hub or integrations." />
      </Box>
    </Box>
  )
}
