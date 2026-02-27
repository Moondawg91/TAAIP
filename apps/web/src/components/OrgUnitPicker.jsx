import React, { useEffect, useState, useRef } from 'react'
import { Box, FormControl, InputLabel, Select, MenuItem, CircularProgress, Typography, Button } from '@mui/material'
import { useOrgSelection } from '../contexts/OrgSelectionContext'
import { apiFetch } from '../api/client'

function sortByDisplay(a,b){
  const A = (a.display_name||'').toUpperCase()
  const B = (b.display_name||'').toUpperCase()
  return A < B ? -1 : A > B ? 1 : 0
}

export default function OrgUnitPicker(){
  const { selection, setSelection } = useOrgSelection()
  const [brigades, setBrigades] = useState([])
  const [bns, setBns] = useState([])
  const [cos, setCos] = useState([])
  const [stns, setStns] = useState([])
  const [loading, setLoading] = useState({ bde:false, bn:false, co:false, stn:false })
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  useEffect(()=>{
    abortRef.current && abortRef.current.abort()
    const ac = new AbortController(); abortRef.current = ac
    setLoading(l=>({ ...l, bde: true }))
    setError(null)
    apiFetch(`/api/v2/org/root`).then(resp => {
      // server returns root + brigades list under data.root and data.brigades
      const arr = (resp && resp.brigades) ? resp.brigades : (resp && resp.units ? resp.units : [])
      arr.sort(sortByDisplay)
      setBrigades(arr)
    }).catch(err=> setError('Failed to load brigades'))
      .finally(()=> setLoading(l=>({ ...l, bde:false })))
    return ()=> ac.abort()
  }, [selection.root_rsid])

  useEffect(()=>{
    // when bde selection changes, load battalions
    if (!selection.bde || !selection.bde.unit_key){ setBns([]); return }
    setLoading(l=>({ ...l, bn:true }))
    setError(null)
    const ac = new AbortController(); abortRef.current = ac
    apiFetch(`/api/v2/org/units?parent_key=${encodeURIComponent(selection.bde.unit_key)}&echelon=BN`)
      .then(resp=>{ const arr = resp && resp.units ? resp.units : (resp || []); arr.sort(sortByDisplay); setBns(arr) })
      .catch(err=> setError('Failed to load battalions'))
      .finally(()=> setLoading(l=>({ ...l, bn:false })))
    return ()=> ac.abort()
  }, [selection.bde_rsid])

  useEffect(()=>{
    if (!selection.bn || !selection.bn.unit_key){ setCos([]); return }
    setLoading(l=>({ ...l, co:true }))
    setError(null)
    const ac = new AbortController(); abortRef.current = ac
    apiFetch(`/api/v2/org/units?parent_key=${encodeURIComponent(selection.bn.unit_key)}&echelon=CO`)
      .then(resp=>{ const arr = resp && resp.units ? resp.units : (resp || []); arr.sort(sortByDisplay); setCos(arr) })
      .catch(err=> setError('Failed to load companies'))
      .finally(()=> setLoading(l=>({ ...l, co:false })))
    return ()=> ac.abort()
  }, [selection.bn_rsid])

  useEffect(()=>{
    if (!selection.co || !selection.co.unit_key){ setStns([]); return }
    setLoading(l=>({ ...l, stn:true }))
    setError(null)
    const ac = new AbortController(); abortRef.current = ac
    apiFetch(`/api/v2/org/units?parent_key=${encodeURIComponent(selection.co.unit_key)}&echelon=STN`)
      .then(resp=>{ const arr = resp && resp.units ? resp.units : (resp || []); arr.sort(sortByDisplay); setStns(arr) })
      .catch(err=> setError('Failed to load stations'))
      .finally(()=> setLoading(l=>({ ...l, stn:false })))
    return ()=> ac.abort()
  }, [selection.co_rsid])

  function update(partial){
    setSelection(prev => ({ ...prev, ...partial }))
  }

  function onBdeChange(e){
    const val = e.target.value || null
    const selObj = val ? { unit_key: val, display_name: (brigades.find(b=>b.rsid===val)||{display_name: val}).display_name } : null
    update({ bde: selObj, bn: null, co: null, stn: null })
  }
  function onBnChange(e){ const val = e.target.value || null; const selObj = val ? { unit_key: val, display_name: (bns.find(b=>b.rsid===val)||{display_name: val}).display_name } : null; update({ bn: selObj, co: null, stn: null }) }
  function onCoChange(e){ const val = e.target.value || null; const selObj = val ? { unit_key: val, display_name: (cos.find(c=>c.rsid===val)||{display_name: val}).display_name } : null; update({ co: selObj, stn: null }) }
  function onStnChange(e){ const val = e.target.value || null; const selObj = val ? { unit_key: val, display_name: (stns.find(s=>s.rsid===val)||{display_name: val}).display_name } : null; update({ stn: selObj }) }

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
      <Typography variant="body2" sx={{ mr:1, fontWeight:500 }}>Unit</Typography>
      <FormControl size="small" sx={{ minWidth:140 }}>
        <InputLabel>Brigade</InputLabel>
        <Select label="Brigade" value={(selection.bde && selection.bde.unit_key) || ''} onChange={onBdeChange}>
          <MenuItem value="">All</MenuItem>
          {loading.bde ? <MenuItem value=""><em>Loading...</em></MenuItem> : brigades.map(b=> <MenuItem key={b.rsid} value={b.rsid}>{b.display_name}</MenuItem>)}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth:140 }}>
        <InputLabel>Battalion</InputLabel>
        <Select label="Battalion" value={(selection.bn && selection.bn.unit_key) || ''} onChange={onBnChange}>
          <MenuItem value="">All</MenuItem>
          {loading.bn ? <MenuItem value=""><em>Loading...</em></MenuItem> : bns.map(n=> <MenuItem key={n.rsid} value={n.rsid}>{n.display_name}</MenuItem>)}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth:140 }}>
        <InputLabel>Company</InputLabel>
        <Select label="Company" value={(selection.co && selection.co.unit_key) || ''} onChange={onCoChange}>
          <MenuItem value="">All</MenuItem>
          {loading.co ? <MenuItem value=""><em>Loading...</em></MenuItem> : cos.map(c=> <MenuItem key={c.rsid} value={c.rsid}>{c.display_name}</MenuItem>)}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth:140 }}>
        <InputLabel>Station</InputLabel>
        <Select label="Station" value={(selection.stn && selection.stn.unit_key) || ''} onChange={onStnChange}>
          <MenuItem value="">All</MenuItem>
          {loading.stn ? <MenuItem value=""><em>Loading...</em></MenuItem> : stns.map(s=> <MenuItem key={s.rsid} value={s.rsid}>{s.display_name}</MenuItem>)}
        </Select>
      </FormControl>

      {error ? <Typography color="error" variant="caption">{error} <Button size="small" onClick={()=> window.location.reload()}>Retry</Button></Typography> : null}
    </Box>
  )
}
