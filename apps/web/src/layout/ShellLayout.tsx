import React from 'react'
import { Box } from '@mui/material'
import NavSidebar from '../components/NavSidebar'
import TopHeader from '../components/TopHeader'
import { Outlet } from 'react-router-dom'

export default function ShellLayout() {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <NavSidebar />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
        <TopHeader />
        <Box component="main" sx={{ p: 2, flex: 1, bgcolor: '#f6f8fa' }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
