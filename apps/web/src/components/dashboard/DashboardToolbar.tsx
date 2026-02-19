import React from 'react'
import { Box, Typography } from '@mui/material'
import FilterBar from './FilterBar'
import ExportMenu from './ExportMenu'

export default function DashboardToolbar({ title, subtitle, filters, onFiltersChange, onExport }:{ title?:string, subtitle?:string, filters?:any, onFiltersChange?: (f:any)=>void, onExport?: (t:string)=>void }){
  return (
    <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:2, mb:2 }}>
      <Box>
        <Typography variant="h5">{title}</Typography>
        {subtitle ? <Typography variant="caption" sx={{ color:'text.secondary' }}>{subtitle}</Typography> : null}
      </Box>

      <Box sx={{ flex:1, display:'flex', justifyContent:'center' }}>
        <FilterBar filters={filters} onChange={(f)=> onFiltersChange ? onFiltersChange(f) : null} />
      </Box>

      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'flex-end' }}>
        <ExportMenu onExport={onExport} />
      </Box>
    </Box>
  )
}
