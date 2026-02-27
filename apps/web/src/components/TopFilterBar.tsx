import React, { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Box, Typography, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import UnitCascadePicker from './UnitCascadePicker'
import { useFilters } from '../contexts/FilterContext'
import useRoutePolicy from '../auth/useRoutePolicy'

type Props = {
  showUnit?: boolean
  showFy?: boolean
  showQtr?: boolean
  extraControls?: React.ReactNode
  title?: string
}

const getFyOptions = () => {
  const y = new Date().getFullYear()
  return [String(y - 1), String(y), String(y + 1)]
}

export default function TopFilterBar({ showUnit = true, showFy = true, showQtr = true, extraControls, title }: Props){
  const loc = useLocation()
  // Determine dashboard pages from canonical route policy
  const policy = useRoutePolicy()
  const isDashboard = Boolean(policy && policy.dashboardPage) || loc.pathname === '/'
  if (!isDashboard) return null
  const { filters, setUnit, setFy, setQtr } = useFilters()
  const [isSticky, setIsSticky] = useState(false)
  const elRef = useRef<HTMLDivElement | null>(null)

  useEffect(()=>{
    const node = elRef.current
    if(!node) return
    const observer = new IntersectionObserver((entries)=>{
      entries.forEach(en => setIsSticky(!en.isIntersecting))
    }, { root: node.parentElement, threshold: [1] })
    // create a sentinel at top
    const sentinel = document.createElement('div')
    sentinel.style.position = 'absolute'
    sentinel.style.top = '0px'
    sentinel.style.left = '0px'
    sentinel.style.width = '1px'
    sentinel.style.height = '1px'
    node.parentElement?.insertBefore(sentinel, node)
    observer.observe(sentinel)
    return ()=>{ observer.disconnect(); sentinel.remove() }
  }, [])

  const fyOptions = getFyOptions()
  const qOptions = ['Q1','Q2','Q3','Q4']

  return (
    <Box ref={elRef} data-sticky={isSticky} sx={{ position: 'sticky', top: 0, zIndex: 10, background: 'background.paper', px:2, py:1, borderBottom: isSticky ? '1px solid rgba(0,0,0,0.08)' : '1px solid rgba(0,0,0,0.02)', boxShadow: isSticky ? '0 2px 8px rgba(0,0,0,0.06)' : 'none' }}>
      <Box sx={{ display:'flex', alignItems:'center', gap:2, justifyContent:'space-between' }}>
        <Box sx={{ display:'flex', alignItems:'center', gap:2 }}>
          {title ? <Typography variant="h6">{title}</Typography> : null}
        </Box>

        <Box sx={{ display:'flex', alignItems:'center', gap:1 }}>
          {(policy && policy.filters && policy.filters.unit) && (
            <UnitCascadePicker value={null} onChange={(sel:any)=>{ const rsid = sel && sel.active && sel.active.rsid ? sel.active.rsid : 'USAREC'; setUnit(rsid) }} dense={true} />
          )}
          {(policy && policy.filters && policy.filters.fy) && (
            <FormControl size="small" sx={{ minWidth:110 }}>
              <InputLabel>FY</InputLabel>
              <Select value={filters.fy} label="FY" onChange={(e)=>setFy(String(e.target.value))}>
                {fyOptions.map(f => <MenuItem key={f} value={f}>{f}</MenuItem>)}
              </Select>
            </FormControl>
          )}
          {(policy && policy.filters && policy.filters.qtr) && (
            <FormControl size="small" sx={{ minWidth:100 }}>
              <InputLabel>Quarter</InputLabel>
              <Select value={filters.qtr} label="Quarter" onChange={(e)=>setQtr(String(e.target.value))}>
                <MenuItem value="">All</MenuItem>
                {qOptions.map(q => <MenuItem key={q} value={q}>{q}</MenuItem>)}
              </Select>
            </FormControl>
          )}
          {(policy && policy.filters && policy.filters.compare) && (
            <FormControl size="small" sx={{ minWidth:120 }}>
              <InputLabel>Compare</InputLabel>
              <Select value={(filters as any).compare || ''} label="Compare" onChange={(e)=>{/* noop - compare persisted via useFilters if implemented */}}>
                <MenuItem value="">None</MenuItem>
                <MenuItem value="A">A</MenuItem>
                <MenuItem value="B">B</MenuItem>
                <MenuItem value="C">C</MenuItem>
              </Select>
            </FormControl>
          )}
          {extraControls}
        </Box>
      </Box>
    </Box>
  )
}
