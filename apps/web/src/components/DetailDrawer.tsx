import React from 'react'
import { Drawer, Box, IconButton, Typography } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'

export default function DetailDrawer({open, onClose, title, children}:{open:boolean, onClose:()=>void, title?:string, children?:any}){
  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{width:520, p:2}}>
        <Box sx={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
          <Typography variant="h6">{title}</Typography>
          <IconButton onClick={onClose}><CloseIcon /></IconButton>
        </Box>
        <Box sx={{mt:2}}>
          {children}
        </Box>
      </Box>
    </Drawer>
  )
}
