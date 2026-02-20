import React from 'react'
import { IconButton, Menu, MenuItem } from '@mui/material'
import GetAppIcon from '@mui/icons-material/GetApp'

type ExportMenuProps = {
  data?: any[]
  filename?: string
}

export default function ExportMenu({data = [], filename = 'export'}: ExportMenuProps){
  const [anchor, setAnchor] = React.useState<null | HTMLElement>(null)
  const open = Boolean(anchor)
  function handleOpen(e: React.MouseEvent<HTMLElement>){ setAnchor(e.currentTarget) }
  function handleClose(){ setAnchor(null) }

  function downloadJSON(){
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${filename}.json`; a.click(); URL.revokeObjectURL(url)
    handleClose()
  }
  function downloadCSV(){
    if(!data || !data.length){ handleClose(); return }
    const keys = Object.keys(data[0])
    const rows = data.map(r => keys.map(k => (`"${String(r[k] ?? '')}"`)).join(','))
    const csv = [keys.join(','), ...rows].join('\n')
    const blob = new Blob([csv], {type: 'text/csv'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${filename}.csv`; a.click(); URL.revokeObjectURL(url)
    handleClose()
  }

  return (
    <>
      <IconButton size="small" onClick={handleOpen} title="Export">
        <GetAppIcon />
      </IconButton>
      <Menu anchorEl={anchor} open={open} onClose={handleClose}>
        <MenuItem onClick={downloadCSV}>Export CSV</MenuItem>
        <MenuItem onClick={downloadJSON}>Export JSON</MenuItem>
        <MenuItem disabled>Export XLSX (coming soon)</MenuItem>
        <MenuItem disabled>Export PDF (coming soon)</MenuItem>
        <MenuItem disabled>Export PPT (coming soon)</MenuItem>
      </Menu>
    </>
  )
}
