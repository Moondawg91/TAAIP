import React from 'react'
import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Box, Divider, ListSubheader, Typography } from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import MapIcon from '@mui/icons-material/Map'
import AssessmentIcon from '@mui/icons-material/Assessment'
import StorageIcon from '@mui/icons-material/Storage'
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings'
import HelpIcon from '@mui/icons-material/Help'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import routePerms from '../rbac/routePerms'

const drawerWidth = 220

const sections = [
  {
    title: 'Dashboard',
    items: [
      { to: '/', label: 'Home', icon: DashboardIcon },
      { to: '/scoreboard', label: 'Scoreboard', icon: AssessmentIcon },
    ],
  },
  {
    title: 'Command Center',
    items: [
      { to: '/command-center', label: 'Overview', icon: AssessmentIcon },
      { to: '/command-center/targeting-data', label: 'Targeting', icon: MapIcon },
      { to: '/command-center/twg', label: 'Targeting (TWG)', icon: MapIcon },
      { to: '/command-center/fusion-cell', label: 'Fusion Cell', icon: AssessmentIcon },
      { to: '/command/mission-feasibility', label: 'Mission Feasibility', icon: AssessmentIcon },
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
    title: 'Planning',
    items: [
      { to: '/planning', label: 'Planning Home', icon: StorageIcon },
      { to: '/planning/twg', label: 'TWG', icon: MapIcon },
      { to: '/planning/fusion', label: 'Fusion Cell', icon: AssessmentIcon },
    ],
  },
  {
    title: 'ROI',
    items: [
      { to: '/roi/marketing', label: 'Marketing ROI', icon: AssessmentIcon },
      { to: '/roi/mac', label: 'MAC ROI', icon: AssessmentIcon },
    ],
  },
  {
    title: 'Data & Documents',
    items: [
      { to: '/data-hub', label: 'Data Hub', icon: StorageIcon },
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
  const { roles, loading, permissions, permissionsObj, hasPerm, isAdmin: ctxIsAdmin } = useAuth()
  const isAdmin = !loading && (ctxIsAdmin || (roles && roles.some(r=>['system_admin','usarec_admin','sysadmin','admin','420t_admin'].includes(r))))

  // determine visibility per-item using route->permission map and admin flag
  const visibleSections = sections.map(s => {
    const items = s.items.filter((it: any) => {
      // keep admin section only for admin if no explicit permission map
      const perm = routePerms[it.to]
      if (!perm) {
        if (s.title === 'Admin' && !isAdmin) return false
        return true
      }
      // if there is a permission mapping, require that permission or admin status
      const allowed = (!loading && (hasPerm && hasPerm(perm))) || isAdmin
      return Boolean((!loading && allowed))
    })
    return { ...s, items }
  }).filter(s => (s.items || []).length > 0)

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
        {visibleSections.map((sec) => (
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
