import React from 'react'
import { IconButton, Menu, MenuItem, Box, Button, ToggleButton, ToggleButtonGroup } from '@mui/material'
import GetAppIcon from '@mui/icons-material/GetApp'
import TableViewIcon from '@mui/icons-material/TableView'
import PrintIcon from '@mui/icons-material/Print'
import DescriptionIcon from '@mui/icons-material/Description'
import SlideshowIcon from '@mui/icons-material/Slideshow'
import { exportToCsv } from '../utils/exportCsv'
import ZeroState from './ZeroState'
import { Table, TableHead, TableRow, TableCell, TableBody, Paper } from '@mui/material'

type Props = {
  title?: string
  data?: any[]
  columns?: Array<string | {key:string,label?:string}>
  tableRows?: any[]
  filenameBase?: string
  filename?: string
  allowPptStub?: boolean
}

function normalizeColumns(columns:any, rows:any[]){
  if(!columns || columns.length===0){
    if(rows && rows.length) return Object.keys(rows[0]).map(k=>({ key:k, label:k }))
    return []
  }
  return columns.map((c:any)=> typeof c === 'string' ? { key:c, label:c } : { key:c.key, label:c.label||c.key })
}

export default function ExportMenu({ title, data = [], columns = [], tableRows, filenameBase = 'export', filename, allowPptStub = true }: Props){
  const [anchor, setAnchor] = React.useState<null | HTMLElement>(null)
  const [viewMode, setViewMode] = React.useState<'dashboard'|'table'>('dashboard')
  const open = Boolean(anchor)
  const rows = tableRows || data || []
  const cols = normalizeColumns(columns, rows)
  const fb = filenameBase || filename || 'export'

  function handleOpen(e: React.MouseEvent<HTMLElement>){ setAnchor(e.currentTarget) }
  function handleClose(){ setAnchor(null) }

  function onDownloadJSON(){
    try{
      const blob = new Blob([JSON.stringify(data || rows || {}, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `${fb}.json`; a.click(); URL.revokeObjectURL(url)
    }catch(e){ console.error(e) }
    handleClose()
  }

  function onDownloadCSV(){
    try{
      exportToCsv(`${fb}.csv`, rows || [], cols)
    }catch(e){ console.error(e) }
    handleClose()
  }

  function onDownloadPDF(){
    try{
      const w = window.open('', '_blank')
      if(!w) return
      const ts = new Date().toISOString()
      let html = `<html><head><title>${title||fb}</title><style>body{background:#F4F6F9;color:#0F1724;font-family:Arial;padding:16px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #E6EEF6;padding:6px;text-align:left}</style></head><body>`
      html += `<h1>${title||fb}</h1><div>${ts}</div>`
      if(rows && rows.length){
        html += '<table><thead><tr>' + (cols.length ? cols.map((c:any)=>`<th>${c.label}</th>`).join('') : Object.keys(rows[0]).map(k=>`<th>${k}</th>`).join('')) + '</tr></thead><tbody>'
        for(const r of rows){
          const cells = cols.length ? cols.map((c:any)=>`<td>${String(r[c.key] ?? '')}</td>`).join('') : Object.keys(r).map(k=>`<td>${String(r[k] ?? '')}</td>`).join('')
          html += `<tr>${cells}</tr>`
        }
        html += '</tbody></table>'
      } else {
        html += '<p>No rows to print</p>'
      }
      html += '</body></html>'
      w.document.write(html)
      w.document.close()
      w.focus()
      setTimeout(()=>{ w.print(); /* do not auto-close to allow user control */ }, 300)
    }catch(e){ console.error(e) }
    handleClose()
  }

  function onDownloadPpt(){
    try{
      const meta = { title: title||fb, timestamp: new Date().toISOString(), rows: rows.slice(0,50) }
      const blob = new Blob([JSON.stringify(meta, null, 2)], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `${fb}.pptx`; a.click(); URL.revokeObjectURL(url)
      if(allowPptStub) alert('PPT export enabled (stub)')
    }catch(e){ console.error(e) }
    handleClose()
  }

  return (
    <Box sx={{ display:'flex', alignItems:'center', gap:1 }}>
      <ToggleButtonGroup size="small" value={viewMode} exclusive onChange={(_,v)=>v && setViewMode(v)} sx={{ bgcolor:'transparent' }}>
        <ToggleButton value="dashboard" sx={{ color:'inherit', borderRadius:2 }}>Dashboard</ToggleButton>
        <ToggleButton value="table" sx={{ color:'inherit', borderRadius:2 }} title="Toggle Table View"><TableViewIcon /></ToggleButton>
      </ToggleButtonGroup>

      <IconButton size="small" onClick={handleOpen} title="Export">
        <GetAppIcon />
      </IconButton>
      <Menu anchorEl={anchor} open={open} onClose={handleClose}>
        <MenuItem onClick={onDownloadCSV}><DescriptionIcon sx={{mr:1}}/> Export CSV</MenuItem>
        <MenuItem onClick={onDownloadJSON}><DescriptionIcon sx={{mr:1}}/> Export JSON</MenuItem>
        <MenuItem onClick={onDownloadPDF}><PrintIcon sx={{mr:1}}/> Export PDF</MenuItem>
        <MenuItem onClick={onDownloadPpt}><SlideshowIcon sx={{mr:1}}/> Export PPT</MenuItem>
      </Menu>

      {viewMode === 'table' ? (
        rows && rows.length ? (
          <Paper sx={{ width: '100%', bgcolor: 'transparent', color: 'inherit', boxShadow: 'none', mt:1 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  { (cols.length ? cols.map((c:any)=>c.label) : (rows[0] ? Object.keys(rows[0]) : [])).map((h:any,i)=> <TableCell key={i} sx={{ color:'text.primary' }}>{h}</TableCell>)}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((r:any,ri:number)=> (
                  <TableRow key={ri}>
                    { (cols.length ? cols.map((c:any)=> r[c.key] ) : Object.keys(r).map(k=> r[k])).map((v:any,ci:number)=> <TableCell key={ci} sx={{ color:'text.secondary' }}>{ typeof v === 'object' ? JSON.stringify(v) : String(v ?? '') }</TableCell>)}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        ) : (
          <ZeroState title="No rows available" message="There are no table rows to display." />
        )
      ) : null }
    </Box>
  )
}
