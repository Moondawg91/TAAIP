import React, { useEffect, useState } from 'react'
import { Box, FormControl, InputLabel, Select, MenuItem, Typography } from '@mui/material'
import { useOrgSelection } from '../contexts/OrgSelectionContext'
import { apiFetch, getOrgChildren } from '../api/client'

function sortByDisplay(a,b){
  const A = (a.display_name||'').toUpperCase()
  const B = (b.display_name||'').toUpperCase()
  return A < B ? -1 : A > B ? 1 : 0
}

export default function UnitCascadePicker({ value, defaultCmdRsid = 'USAREC', onChange, dense=false, disabled=false, className='' }){
  const { selection, setBde, setBn, setCo, setStn, resetToUsarec } = useOrgSelection()
  const sel = value || selection

  const [brigades, setBrigades] = useState([])
  const [bns, setBns] = useState([])
  const [cos, setCos] = useState([])
  const [stns, setStns] = useState([])
  const [loadingBdes, setLoadingBdes] = useState(false)
  const [loadingBns, setLoadingBns] = useState(false)
  const [loadingCos, setLoadingCos] = useState(false)
  const [loadingStns, setLoadingStns] = useState(false)

  useEffect(()=>{
    let mounted = true
    // use configured root (from selection or default)
    const root = (sel && sel.root_rsid) ? sel.root_rsid : defaultCmdRsid
    setLoadingBdes(true)
    getOrgChildren(root, 'BDE').then(arr => {
      if (!mounted) return
      const list = Array.isArray(arr) ? arr : []
      list.sort(sortByDisplay)
      setBrigades(list)
    }).catch(()=> setBrigades([])).finally(()=>{ if (mounted) setLoadingBdes(false) })
    return ()=>{ mounted = false }
  }, [sel && sel.root_rsid, defaultCmdRsid])

  useEffect(()=>{
    if (!sel || !sel.bde || !sel.bde.rsid){ setBns([]); return }
    setLoadingBns(true)
    getOrgChildren(sel.bde.rsid, 'BN')
      .then(arr=>{ const list = Array.isArray(arr) ? arr : []; list.sort(sortByDisplay); setBns(list) })
      .catch(()=> setBns([])).finally(()=> setLoadingBns(false))
  }, [sel && sel.bde && sel.bde.rsid])

  useEffect(()=>{
    if (!sel || !sel.bn || !sel.bn.rsid){ setCos([]); return }
    setLoadingCos(true)
    getOrgChildren(sel.bn.rsid, 'CO')
      .then(arr=>{ const list = Array.isArray(arr) ? arr : []; list.sort(sortByDisplay); setCos(list) })
      .catch(()=> setCos([])).finally(()=> setLoadingCos(false))
  }, [sel && sel.bn && sel.bn.rsid])

  useEffect(()=>{
    if (!sel || !sel.co || !sel.co.rsid){ setStns([]); return }
    setLoadingStns(true)
    getOrgChildren(sel.co.rsid, 'STN')
      .then(arr=>{ const list = Array.isArray(arr) ? arr : []; list.sort(sortByDisplay); setStns(list) })
      .catch(()=> setStns([])).finally(()=> setLoadingStns(false))
  }, [sel && sel.co && sel.co.rsid])

  function emit(next){
    const payload = Object.assign({}, next)
    if (onChange) onChange(payload)
    else {
      // use provided context setters to persist change
      // determine which level changed by comparing rsids
      try{
        // prefer calling the deepest setter available
        if (payload.stn && payload.stn.rsid) return setStn(payload.stn)
        if (payload.co && payload.co.rsid) return setCo(payload.co)
        if (payload.bn && payload.bn.rsid) return setBn(payload.bn)
        if (payload.bde && payload.bde.rsid) return setBde(payload.bde)
        // fallback reset
        return resetToUsarec()
      }catch(e){ /* ignore */ }
    }
  }

  function _nodeFromList(list, key){
    if (!key) return null
    return list.find(x => (x.rsid && x.rsid === key) || (x.unit_key && x.unit_key === key) || (x.unit_key && x.unit_key === key)) || null
  }

  function onBdeChange(e){
    const key = e.target.value || null
    const node = key ? _nodeFromList(brigades, key) : null
    const bde = node ? { rsid: node.rsid || node.unit_key, display_name: node.display_name, echelon: node.echelon || node.echelon_type } : null
    emit({ ...sel, bde, bn: null, co: null, stn: null })
  }
  function onBnChange(e){ const key = e.target.value || null; const node = key ? _nodeFromList(bns, key) : null; const bn = node ? { rsid: node.rsid || node.unit_key, display_name: node.display_name, echelon: node.echelon || node.echelon_type } : null; emit({ ...sel, bn, co: null, stn: null }) }
  function onCoChange(e){ const key = e.target.value || null; const node = key ? _nodeFromList(cos, key) : null; const co = node ? { rsid: node.rsid || node.unit_key, display_name: node.display_name, echelon: node.echelon || node.echelon_type } : null; emit({ ...sel, co, stn: null }) }
  function onStnChange(e){ const key = e.target.value || null; const node = key ? _nodeFromList(stns, key) : null; const stn = node ? { rsid: node.rsid || node.unit_key, display_name: node.display_name, echelon: node.echelon || node.echelon_type } : null; emit({ ...sel, stn }) }

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }} className={className}>
      <Typography variant="body2" sx={{ mr:1, fontWeight:500 }}>Unit</Typography>
      <Box sx={{ bgcolor: 'primary.dark', color: 'white', px:1, py:0.5, borderRadius: 1, mr:1, fontSize:12 }}>{sel && sel.root_rsid ? sel.root_rsid : defaultCmdRsid}</Box>
      <FormControl size={dense ? 'small' : 'medium'} sx={{ minWidth:140 }}>
        <InputLabel>BDE</InputLabel>
        <Select label="BDE" value={(sel && sel.bde && (sel.bde.rsid || sel.bde.unit_key)) || ''} onChange={onBdeChange} disabled={disabled || loadingBdes}>
          <MenuItem value="">All</MenuItem>
          {loadingBdes ? <MenuItem value="" disabled>Loading...</MenuItem> : (brigades.length ? brigades.map(b=> <MenuItem key={(b.rsid||b.unit_key)} value={(b.rsid||b.unit_key)}>{b.display_name}</MenuItem>) : <MenuItem value="" disabled>No units found</MenuItem>)}
        </Select>
      </FormControl>

      <FormControl size={dense ? 'small' : 'medium'} sx={{ minWidth:140 }}>
        <InputLabel>BN</InputLabel>
        <Select label="BN" value={(sel && sel.bn && (sel.bn.rsid || sel.bn.unit_key)) || ''} onChange={onBnChange} disabled={!sel || !sel.bde || disabled || loadingBns}>
          <MenuItem value="">All</MenuItem>
          {loadingBns ? <MenuItem value="" disabled>Loading...</MenuItem> : (bns.length ? bns.map(n=> <MenuItem key={(n.rsid||n.unit_key)} value={(n.rsid||n.unit_key)}>{n.display_name}</MenuItem>) : <MenuItem value="" disabled>No units found</MenuItem>)}
        </Select>
      </FormControl>

      <FormControl size={dense ? 'small' : 'medium'} sx={{ minWidth:140 }}>
        <InputLabel>CO</InputLabel>
        <Select label="CO" value={(sel && sel.co && (sel.co.rsid || sel.co.unit_key)) || ''} onChange={onCoChange} disabled={!sel || !sel.bn || disabled || loadingCos}>
          <MenuItem value="">All</MenuItem>
          {loadingCos ? <MenuItem value="" disabled>Loading...</MenuItem> : (cos.length ? cos.map(c=> <MenuItem key={(c.rsid||c.unit_key)} value={(c.rsid||c.unit_key)}>{c.display_name}</MenuItem>) : <MenuItem value="" disabled>No units found</MenuItem>)}
        </Select>
      </FormControl>

      <FormControl size={dense ? 'small' : 'medium'} sx={{ minWidth:140 }}>
        <InputLabel>STN</InputLabel>
        <Select label="STN" value={(sel && sel.stn && (sel.stn.rsid || sel.stn.unit_key)) || ''} onChange={onStnChange} disabled={!sel || !sel.co || disabled || loadingStns}>
          <MenuItem value="">All</MenuItem>
          {loadingStns ? <MenuItem value="" disabled>Loading...</MenuItem> : (stns.length ? stns.map(s=> <MenuItem key={(s.rsid||s.unit_key)} value={(s.rsid||s.unit_key)}>{s.display_name}</MenuItem>) : <MenuItem value="" disabled>No units found</MenuItem>)}
        </Select>
      </FormControl>
    </Box>
  )
}
