import React, { useState } from 'react'
import { AppBar, Toolbar, Typography, Box, Menu, MenuItem, IconButton, Divider } from '@mui/material'
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown'
import { alpha } from '@mui/material'
import AccountCircleIcon from '@mui/icons-material/AccountCircle'
import LockIcon from '@mui/icons-material/Lock'

export default function TopHeader({ title }: { title?: string }){
  const [anchor, setAnchor] = useState<null | HTMLElement>(null)

  return (
    <Box>
      <AppBar position="static" color="default" elevation={0} sx={{ background: (theme)=> `linear-gradient(90deg, ${alpha('#7C4DFF',0.08)}, transparent)`, borderBottom: `1px solid rgba(255,255,255,0.06)` }}>
        <Toolbar sx={{minHeight:64, px:2, bgcolor: 'background.paper'}}>
          <Box sx={{display:'flex', alignItems:'center', gap:2, flex:1}}>
            <Box>
              <Typography variant="h6" sx={{color:'text.primary', fontWeight:700}}>TAAIP</Typography>
              <Typography variant="caption" sx={{color:'text.secondary'}}>Talent Acquisition Intelligence & Analytics Platform</Typography>
            </Box>
          </Box>

          <Box sx={{display:'flex', alignItems:'center', gap:1}}>
            <IconButton size="small" onClick={(e)=>setAnchor(e.currentTarget)} sx={{color:'text.primary'}}>
              <AccountCircleIcon />
            </IconButton>
            <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={()=>setAnchor(null)}>
              <MenuItem onClick={()=>setAnchor(null)}><LockIcon sx={{mr:1}} /> Roles</MenuItem>
              <MenuItem onClick={()=>setAnchor(null)}>Preferences</MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
    </Box>
  )
}
