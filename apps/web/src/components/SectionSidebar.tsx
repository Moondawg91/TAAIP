import React, { useState, useEffect, useRef } from 'react'
import { Box, IconButton, Typography, List, ListItemButton, ListItemIcon, ListItemText, Tooltip, Divider } from '@mui/material'
import * as Icons from '@mui/icons-material'
import NAV_CONFIG from '../nav/navConfig'
import permissionMap from '../auth/permissionMap'
import ROUTE_POLICIES from '../auth/routePolicy'
import { useAuth } from '../contexts/AuthContext'
import accessHelper from '../auth/accessHelper'
import PushPinIcon from '@mui/icons-material/PushPin'
import CloseIcon from '@mui/icons-material/Close'
import MenuIcon from '@mui/icons-material/Menu'
import LockIcon from '@mui/icons-material/Lock'
import { useNavigate, useLocation } from 'react-router-dom'

function IconByName(name: string) {
  // @ts-ignore
  const C = Icons[name] || Icons['Widgets']
  return <C fontSize="small" />
}

type NavItem = { id: string; label: string; path?: string; icon?: string; disabled?: boolean }
type NavSection = { id: string; label: string; icon?: string; items: NavItem[] }

export default function SectionSidebar(){
  const [pinned, setPinned] = useState<boolean>(() => {
    try { return localStorage.getItem('taaip_sidebar_pinned') === 'true' } catch { return false }
  })
  const [explicitOpen, setExplicitOpen] = useState<boolean>(false)
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const navigate = useNavigate()
  const loc = useLocation()
  const auth = useAuth()

  // Ensure the active section reflects the current route so sidebar shows correct group
  useEffect(()=>{
    try {
      const p = loc.pathname || ''
      let matched: string | null = null
      for (const s of (NAV_CONFIG as unknown as NavSection[])){
        if (!s || !s.items) continue
        for (const it of s.items){
          if (it.path && typeof it.path === 'string' && p.startsWith(it.path)){
            matched = s.id
            break
          }
        }
        if (matched) break
      }
      if (matched) setActiveSection(matched)
    } catch(e) {
      // noop
    }
  }, [loc.pathname])

  // derive roles from auth context for admin checks
  const userRoles = (auth && auth.roles) ? auth.roles.map(r=>String(r).toLowerCase()) : []

  useEffect(()=>{
    try { localStorage.setItem('taaip_sidebar_pinned', pinned ? 'true' : 'false') } catch {}
  }, [pinned])

  const collapsedWidth = 72
  const expandedWidth = 280
  const open = pinned || explicitOpen

  // Always show all sections per UX requirements. Items will be shown locked when access is missing.
  const visibleNav = (NAV_CONFIG as unknown as NavSection[])

  // access checks are evaluated per-item using accessHelper

  // tempSection removed; collapsed icon click directly sets activeSection and expands

  return (
    <Box sx={{ width: open ? expandedWidth : collapsedWidth, transition: 'width 220ms cubic-bezier(.2,0,.2,1)', bgcolor: 'background.paper', color: 'text.primary', display: 'flex', flexDirection: 'column', borderRight: `1px solid rgba(255,255,255,0.04)` }}>
      <Box sx={{ display:'flex', alignItems:'center', px:2, py:1, gap:2 }}>
          <Box sx={{ display:'flex', alignItems:'center', gap:1, flex:1 }}>
          <Typography variant="h6" sx={{ fontWeight:700, cursor: 'pointer' }} onClick={()=>navigate('/')}>{/* keep short */}TAAIP</Typography>
          {open && <Typography variant="caption" sx={{ color:'text.secondary' }}>Talent Acquisition Intelligence & Analytics Platform</Typography>}
        </Box>
        <IconButton size="small" onClick={()=>setPinned(p=>!p)} sx={{ color:'text.secondary' }}>
          {pinned ? <PushPinIcon /> : <MenuIcon />}
        </IconButton>
      </Box>

      <Divider sx={{ borderColor: 'divider' }} />

      {/* Section quick icons when collapsed */}
      {!open && (
        <Box sx={{ display:'flex', flexDirection:'column', alignItems:'center', gap:1, py:1 }}>
          {visibleNav.map(section => (
            <Tooltip key={section.id} title={section.label} placement="right">
                <IconButton
                  onClick={() => {
                    // toggle explicit open state and set active section on click
                    setExplicitOpen(o => !o)
                    setActiveSection(section.id)
                    try {
                      const first = (section.items || []).find((i: NavItem) => {
                        if (!i.path || typeof i.path !== 'string' || i.path.length<=1) return false
                        return true
                      })
                      if (first && typeof first.path === 'string') {
                        navigate(first.path)
                      }
                    } catch (e) { }
                  }}
                  sx={{ color:'text.secondary' }}>
                {IconByName(section.icon)}
              </IconButton>
            </Tooltip>
          ))}
        </Box>
      )}

      <Box sx={{ flex:1, overflow:'auto', py:1 }}>
        {visibleNav.map(section => {
          const showItems = open && (activeSection ? section.id === activeSection : section.id === 'command-center')
          return (
            <Box key={section.id} sx={{ px: open ? 2 : 0, mb:1 }} id={`${section.id}-section`} onMouseEnter={() => { if (open) setActiveSection(section.id) }}>
              {open && <Typography variant="overline" sx={{ color:'text.secondary', cursor: 'pointer' }} onClick={() => setActiveSection(section.id)}>{section.label}</Typography>}
              {showItems ? (
                <List>
                  {section.items.map((it:NavItem)=> {
                    const path = it.path || ''
                    const permsSource = (auth && auth.permissionsObj && Object.keys(auth.permissionsObj).length) ? Object.keys(auth.permissionsObj) : auth.permissions
                    const access = accessHelper.canAccessForPath(permsSource, path)
                    // respect auth.hasPerm for fine-grained gating; allow if accessHelper allows or if any missing perms are granted via hasPerm
                    const disabledForUser = !(access.allowed || (auth && auth.hasPerm && access.missing && access.missing.some((m:any)=> auth.hasPerm(m))))
                    return (
                      <Tooltip key={it.path || it.id} title={!open ? it.label : ''} placement="right">
                              <ListItemButton
                                selected={loc.pathname===it.path}
                                onClick={()=>{
                                  if (!path) return
                                  if (auth.loading) return
                                  if (disabledForUser) {
                                    // navigate to unauthorized page with missing perms and requested path
                                    try { navigate('/unauthorized', { state: { missing: access.missing || [], path } }) } catch(e){ }
                                    return
                                  }
                                  navigate(path)
                                }}
                                disabled={auth.loading}
                                sx={{ borderRadius:1, my:0.5, px: open ? 1.5 : 0.5, opacity: auth.loading ? 0.6 : 1 }}>
                          <ListItemIcon sx={{ minWidth: open ? 40 : 0, justifyContent:'center', color: disabledForUser ? 'text.disabled' : 'primary.main' }}>{ IconByName(it.icon) }</ListItemIcon>
                          {open && <ListItemText primary={it.label} primaryTypographyProps={{ variant:'body2' }} />}
                          { (disabledForUser && open) ? <LockIcon fontSize="small" sx={{ ml:1, color:'text.secondary' }} /> : null }
                        </ListItemButton>
                      </Tooltip>
                    )
                  })}
                </List>
              ) : (
                // show nothing (collapsed header only)
                null
              )}
              <Divider sx={{ my:1, borderColor:'divider' }} />
            </Box>
          )
        })}
      </Box>

      <Divider sx={{ borderColor: 'divider' }} />
      <Box sx={{ px:2, py:1 }}>
        {open && <Typography variant="caption" sx={{ color:'text.secondary' }}>© 2026 TAAIP — Talent Acquisition Intelligence & Analytics Platform</Typography>}
      </Box>
    </Box>
  )
}
