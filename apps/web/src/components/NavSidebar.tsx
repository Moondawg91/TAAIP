import React from 'react'
import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Box, Divider } from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import MapIcon from '@mui/icons-material/Map'
import AssessmentIcon from '@mui/icons-material/Assessment'
import StorageIcon from '@mui/icons-material/Storage'
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings'
import HelpIcon from '@mui/icons-material/Help'
import { Link as RouterLink, useLocation } from 'react-router-dom'

const drawerWidth = 220

const items = [
  { to: '/', label: 'Home', icon: DashboardIcon },
  { to: '/dashboard', label: 'Dashboard', icon: AssessmentIcon },
  { to: '/dashboards/command-center', label: 'Command Center', icon: AssessmentIcon },
  { to: '/coverage', label: 'Coverage', icon: MapIcon },
  { to: '/geo', label: 'Geo Intelligence', icon: MapIcon },
  { to: '/market', label: 'Market Potential', icon: StorageIcon },
  { to: '/production', label: 'Production', icon: AssessmentIcon },
  { to: '/ingest', label: 'Ingest / Data', icon: StorageIcon },
  { to: '/import-center', label: 'Import Center', icon: StorageIcon },
  { to: '/qbr', label: 'QBR / Boards', icon: AssessmentIcon },
  { to: '/projects', label: 'Projects', icon: AssessmentIcon },
  { to: '/meetings', label: 'Fusion Cell', icon: AdminPanelSettingsIcon },
  { to: '/calendar', label: 'Calendar', icon: MapIcon },
  { to: '/admin', label: 'Admin', icon: AdminPanelSettingsIcon },
  { to: '/help', label: 'Help Desk', icon: HelpIcon },
]

export default function NavSidebar(){
  const location = useLocation()
  return (
    <Drawer variant="permanent" sx={{ width: drawerWidth, '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' } }}>
      <Toolbar sx={{px:2}}>
        <Box>
          <strong>TAAIP</strong>
          <div style={{fontSize:12, color:'#666'}}>Analytics</div>
        </Box>
      </Toolbar>
      <Divider />
      <List>
        {items.map((it) => {
          const Icon = it.icon
          return (
            <ListItemButton key={it.to} component={RouterLink} to={it.to} selected={location.pathname === it.to}>
              <ListItemIcon><Icon /></ListItemIcon>
              <ListItemText primary={it.label} />
            </ListItemButton>
          )
        })}
      </List>
    </Drawer>
  )
}
