import React from 'react'
import { Button, Menu, MenuItem } from '@mui/material'

export default function ExportMenu({ onExport }:{ onExport?: (t:string)=>void }){
  const [anchor, setAnchor] = React.useState<null | HTMLElement>(null)
  const open = Boolean(anchor)
  const handleClick = (e:React.MouseEvent<HTMLElement>)=> setAnchor(e.currentTarget)
  const close = ()=> setAnchor(null)
  const doExport = (t:string)=>{ close(); if(onExport) onExport(t); else window.dispatchEvent(new CustomEvent('taaipexport', { detail: { type: t }})); }

  return (
    <div>
      <Button size="small" variant="outlined" onClick={handleClick}>Export</Button>
      <Menu anchorEl={anchor} open={open} onClose={close}>
        <MenuItem onClick={()=>doExport('csv')}>CSV</MenuItem>
        <MenuItem onClick={()=>doExport('xlsx')}>XLSX</MenuItem>
        <MenuItem onClick={()=>doExport('pdf')}>PDF</MenuItem>
        <MenuItem onClick={()=>doExport('json')}>JSON</MenuItem>
        <MenuItem onClick={()=>doExport('ppt')}>PPT</MenuItem>
      </Menu>
    </div>
  )
}
