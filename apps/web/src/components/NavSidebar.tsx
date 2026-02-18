import React from 'react'
import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Box, Divider, ListSubheader, Typography } from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import MapIcon from '@mui/icons-material/Map'
import AssessmentIcon from '@mui/icons-material/Assessment'
import StorageIcon from '@mui/icons-material/Storage'
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings'
import HelpIcon from '@mui/icons-material/Help'
import { Link as RouterLink, useLocation } from 'react-router-dom'

const drawerWidth = 220

const sections = [
  {
    title: 'Dashboard',
    items: [
      { to: '/', label: 'Home', icon: DashboardIcon },
      { to: '/command-center', label: 'Command Center', icon: AssessmentIcon },
      { to: '/scoreboard', label: 'Scoreboard', icon: AssessmentIcon },
    ],
  },
  {
    title: 'Operations',
    items: [
      { to: '/events', label: 'Event Ops', icon: AssessmentIcon },
      { to: '/projects', label: 'Project Ops', icon: AssessmentIcon },
      { to: '/working-groups', label: 'Working Groups', icon: AdminPanelSettingsIcon },
    ],
  },
  {
    title: 'Planning & Resources',
    items: [
      { to: '/budgets', label: 'Budgets', icon: StorageIcon },
      { to: '/reports', label: 'Reports (QBR)', icon: AssessmentIcon },
    ],
  },
  {
    title: 'Data & Documents',
    items: [
      { to: '/import-center', label: 'Import Center', icon: StorageIcon },
      { to: '/docs', label: 'Document Library', icon: HelpIcon },
      { to: '/training', label: 'Training (LMS)', icon: AssessmentIcon },
    ],
  },
  {
    title: 'Admin',
    items: [
      { to: '/admin', label: 'Administration', icon: AdminPanelSettingsIcon },
    ],
  },
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
        {sections.map((sec) => (
          <Box key={sec.title} sx={{mb:1}}>
            <ListSubheader disableSticky sx={{bgcolor:'transparent'}}>
              <Typography variant="subtitle2" sx={{pl:1, color:'#666'}}>{sec.title}</Typography>
            </ListSubheader>
            {sec.items.map((it: any) => {
              const Icon = it.icon
              return (
                <ListItemButton key={it.to} component={RouterLink} to={it.to} selected={location.pathname === it.to}>
                  <ListItemIcon><Icon /></ListItemIcon>
                  <ListItemText primary={it.label} />
                </ListItemButton>
              )
            })}
            <Divider sx={{my:1}} />
          </Box>
        ))}
      </List>
    </Drawer>
  )
}
