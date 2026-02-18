import React, { useState, useEffect, useRef } from 'react'
import { Box, IconButton, Typography, List, ListItemButton, ListItemIcon, ListItemText, Tooltip, Divider } from '@mui/material'
import * as Icons from '@mui/icons-material'
import NAV_CONFIG from '../nav/navConfig'
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
  const [hovered, setHovered] = useState<boolean>(false)
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const navigate = useNavigate()
  const loc = useLocation()

  useEffect(()=>{
    try { localStorage.setItem('taaip_sidebar_pinned', pinned ? 'true' : 'false') } catch {}
  }, [pinned])

  const collapsedWidth = 72
  const expandedWidth = 280
  const open = pinned || hovered

  // tempSection removed; collapsed icon click directly sets activeSection and expands

  return (
    <Box sx={{ width: open ? expandedWidth : collapsedWidth, transition: 'width 220ms cubic-bezier(.2,0,.2,1)', bgcolor: 'background.paper', color: 'text.primary', display: 'flex', flexDirection: 'column', borderRight: `1px solid rgba(255,255,255,0.04)` }} onMouseEnter={()=>setHovered(true)} onMouseLeave={()=>{ setHovered(false); if(!pinned) setActiveSection(null) }}>
      <Box sx={{ display:'flex', alignItems:'center', px:2, py:1, gap:2 }}>
        <Box sx={{ display:'flex', alignItems:'center', gap:1, flex:1 }}>
          <Typography variant="h6" sx={{ fontWeight:700 }}>{/* keep short */}TAAIP</Typography>
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
          {(NAV_CONFIG as unknown as NavSection[]).map(section => (
            <Tooltip key={section.id} title={section.label} placement="right">
              <IconButton onClick={() => {
                // expand the sidebar
                setHovered(true)
                // toggle active section (off if already active)
                setActiveSection(prev => (prev === section.id ? null : section.id))

                // navigate to first enabled item if available
                try {
                  const first = (section.items || []).find((i: NavItem) => !i.disabled && typeof i.path === 'string' && i.path.length > 1)
                  if (first && typeof first.path === 'string') {
                    navigate(first.path)
                  }
                } catch (e) {
                  // noop
                }

                // do not auto-collapse via timeout; collapse happens on mouse leave
              }} sx={{ color:'text.secondary' }}>
                {IconByName(section.icon)}
              </IconButton>
            </Tooltip>
          ))}
        </Box>
      )}

      <Box sx={{ flex:1, overflow:'auto', py:1 }}>
        {(NAV_CONFIG as unknown as NavSection[]).map(section => {
          const showItems = open && (activeSection ? section.id === activeSection : section.id === 'command-center')
          return (
            <Box key={section.id} sx={{ px: open ? 2 : 0, mb:1 }} id={`${section.id}-section`}>
              {open && <Typography variant="overline" sx={{ color:'text.secondary' }}>{section.label}</Typography>}
              {showItems ? (
                <List>
                  {section.items.map((it:NavItem)=> (
                    <Tooltip key={it.path || it.id} title={!open ? it.label : ''} placement="right">
                      <ListItemButton selected={loc.pathname===it.path} onClick={()=>!it.disabled && navigate(it.path)} disabled={it.disabled} sx={{ borderRadius:1, my:0.5, px: open ? 1.5 : 0.5 }}>
                        <ListItemIcon sx={{ minWidth: open ? 40 : 0, justifyContent:'center', color: it.disabled ? 'text.secondary' : 'primary.main' }}>{ it.disabled ? <LockIcon fontSize="small" /> : IconByName(it.icon) }</ListItemIcon>
                        {open && <ListItemText primary={it.label} primaryTypographyProps={{ variant:'body2' }} secondary={it.disabled ? 'Coming soon' : undefined} />}
                      </ListItemButton>
                    </Tooltip>
                  ))}
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
