import React from 'react'
import { Box, Typography } from '@mui/material'
import EmptyState from '../../components/common/EmptyState'

export default function ProjectsEventsPage(){
  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h4">Event + Project Management</Typography>
      <EmptyState title="Coming soon" subtitle="Project & Event management features are in progress." />
    </Box>
  )
}
